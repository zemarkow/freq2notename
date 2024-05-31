## Module Description
#
# Author: Zachary E. Markow
# Written 27 June 2023.
# Last Updated 30 May 2024.
#
# Convert note names to frequencies in Hz and vice versa.
#
# Update Log:
#
# - 5/30/2024: Replaced \ with \\ in many regular expression strings
# to address warnings about \... not being a valid escape sequence.
#
# - 5/26/2024: Fixed bug where cents deviations were calculated
# incorrectly for transposing instruments. Also added some
# instruments to the list of presets for transposition.
#
# - 5/8/2024: Added support for fancy Unicode flat (♭) and
# sharp (♯) symbols.
#
# - 4/24/2024: Added ability to transpose note names. Moved
# the conversion from note name integer representations
# to note name into a separate function called intParts2NoteName.
#
# - 4/14/2024: Added / to the list of recognized frequency
# and note name separators when processing block text.
#
# - 4/6/2024: Changed names_already_trimmed input to
# names_already_trimmed_uppercase for the key_sig_guess function
# and generalized that function to handle inputs where the note
# names' first characters are not necessarily uppercase.
# Also added the block_extract_note_name_letters_list function.
# Also changed the default setting of all use_flats flags to True.
#
# - 3/31/2024: Added block_convert_notes2freqs function to convert
# note names to frequencies in a block of text. Also added | to
# the list of allowed characters between adjacent notes in a line
# of the block text inputs to block_convert_notes2freqs and
# block_convert_freqs2notes. Also added the option to output lists
# of all frequencies and note names encountered in the block text.
#
# - 3/27/2024: Added block_convert_freqs2notes function to convert
# frequencies to note names in a block of text.
#
# - 3/15/2024: Updated noteName2Freq to handle a wider range
# of note name formats.
#
# - 3/10/2024: Added flexibility to output of freq2note.
# Also added functions to automatically estimate the A4 frequency
# from a list of note frequencies. Also added a function to
# guess the major key signature that best fits a list of notes.
#


# Import needed items.

from math import log2, ceil
import re
from os import linesep as os_linesep


# Note name conversion functions.

def noteLetter2IdxKeyInOctave(keyFormat="lists"):
    # m = Number of half-steps away from A within octave.
    if keyFormat == "dict":
        key = {'C':-9, 'C#':-8, 'Db':-8, 'D':-7, 'D#':-6, 'Eb':-6, 'E':-5, 'Fb':-5, 'F':-4, 'E#':-4, 'F#':-3, 'Gb':-3, 'G':-2, 'G#':-1, 'Ab':-1, 'A':0, 'A#':1, 'Bb':1, 'B':2, 'B#':3, 'Cb':-10}
        return key
    elif keyFormat == "lists":
        key_names = ['C','C#','Db','D','D#','Eb','E','Fb','F','E#','F#','Gb','G','G#','Ab','A','A#','Bb','B','B#','Cb']
        key_idx_m = [-9, -8,  -8,  -7, -6,  -6,  -5, -5,  -4, -4,  -3,  -3,  -2, -1,  -1,  0,  1,   1,   2,  3,   -10]
        return key_names, key_idx_m


def note2freq(noteName, refFreqA4_Hz=440, includeExtraOutputs=False, inst_transp_hsteps=0):

    # noteName is assumed to be at concert pitch (instrument in the key of C)
    # unless inst_transp_hsteps is nonzero. inst_transp_hsteps is the
    # (possibly negative) integer number of half-steps that the instrument
    # shifts notes from concert pitch. So, for example, for a typical Western
    # Bb clarinet, inst_transp_hsteps would be -2. When inst_transp_hsteps
    # is nonzero, noteName is interpreted as the name of the written note
    # played by the instrument.

    # Acceptable input format examples:
    # "E2 - 10 cents"
    # "F6+21cents"
    # "Ab3-14"
    # "E#-1+3"
    # "a-1 + 5"

    # When includeExtraOutputs is True, this function returns a dictionary
    # (outDict) of items instead of only the note frequency. In that case:
    # outDict["freq"] = note frequency
    # outDict["hsteps_from_A4"] = k (defined below)
    # outDict["octave_n"] = n (defined below)
    # outDict["hsteps_from_An"] = m (defined below)
    # outDict["cents"] = c (defined below)
    # outDict["cents_text"] = text containing the cents deviation
    
    # k = Number of half-steps away from A4.
    # n = Octave number.
    # m = Number of half-steps away from A within octave.
    # k = 12(n-4) + m
    # c = Cents away from k.
    # freq_Hz = refFreqA4_Hz * (2 ** (k/12 + c/1200))

    # Replace any fancy Unicode flat or sharp symbols with simple b or #.
    # Eliminate any fancy natural symbols.
    if "♭" in noteName:
        noteNamePreproc = "b".join(noteName.split("♭"))
    elif "♯" in noteName:
        noteNamePreproc = "#".join(noteName.split("♯"))
    elif "♮" in noteName:
        noteNamePreproc = "".join(noteName.split("♮"))
    else:  # No fancy flat, sharp, or natural symbols present.
        noteNamePreproc = noteName

    # First check for +/- signs and split by them, keeping them for later use.
    noteNameSplitPM = re.split("([+-])", noteNamePreproc)

    # Remove whitespace in component strings.
    noteNameSplitPM = [s.strip() for s in noteNameSplitPM]

    if len(noteNameSplitPM) == 1:  # Case 1: No +/- signs are present.
        # In this case, we have a simple "Xn" note with no cents deviation and n >= 0.
        # Split into letter name and octave number.
        matchObj = re.search("[0-9]", noteNameSplitPM[0])
        noteLetter = noteNameSplitPM[0][0:matchObj.start(0)].strip()
        noteLetter = noteLetter[0].upper() + noteLetter[1:]  # Ensure main note letter component is uppercase for noteLetter2IdxKeyInOctave later.
        n = int(noteNameSplitPM[0][matchObj.start(0):])  # Octave number.
        c = 0  # Cents deviation.

    elif len(noteNameSplitPM) == 3:  # Case 2: Exactly one +/- sign is present.
        if re.match("[0-9]", noteNameSplitPM[0][-1]) is None:
            # Case 2a: The character just before the +/- sign is not a number and is therefore a note letter, a flat (b), or a sharp (#), so the number following the +/- sign is an octave number, and there is no cents deviation.
            # Example: "X-y" with y > 0.
            noteLetter = noteNameSplitPM[0]
            noteLetter = noteLetter[0].upper() + noteLetter[1:]  # Ensure main note letter component is uppercase for noteLetter2IdxKeyInOctave later.
            n = int("".join(noteNameSplitPM[1:])) # Octave number.
            c = 0  # Cents deviation.

        else:
            # Case 2b: The character just before the +/- sign is a number and therefore must be part of the octave number, and the number after the +/- sign is the cents deviation number.
            # Example: "Xn - z cents" with n >= 0 and z >= 0.
            matchObj = re.search("[0-9]", noteNameSplitPM[0])
            noteLetter = noteNameSplitPM[0][0:matchObj.start(0)].strip()
            noteLetter = noteLetter[0].upper() + noteLetter[1:]  # Ensure main note letter component is uppercase for noteLetter2IdxKeyInOctave later.
            n = int(noteNameSplitPM[0][matchObj.start(0):])  # Octave number.
            cPlusExtra = "".join(noteNameSplitPM[1:])  # Possibly includes extra characters after the cents deviation, such as " cents".
            c = re.split("[a-zA-Z]", cPlusExtra)[0]  # Discard extra letters.
            c = float(c.strip())  # Cents deviation.
    
    elif len(noteNameSplitPM) == 5:  # Case 3: Exactly two +/- signs are present.
        # Here, the number after and including the first +/- sign is the octave number, and the number after and including the second +/- is the cents deviation number.
        # Example: "X#-y+z cents" with y >= 0 and z >= 0.
        noteLetter = noteNameSplitPM[0]
        noteLetter = noteLetter[0].upper() + noteLetter[1:]  # Ensure main note letter component is uppercase for noteLetter2IdxKeyInOctave later.
        n = int("".join(noteNameSplitPM[1:3]))  # Octave number.
        cPlusExtra = "".join(noteNameSplitPM[3:])  # Possibly includes extra characters after the cents deviation number, such as " cents".
        c = re.split("[a-zA-Z]", cPlusExtra)[0]  # Discard extra letters.
        c = float(c.strip())  # Cents deviation.

    else:
        raise ValueError("Unsupported noteName format.")
        
    # Convert note letter into number m within octave.
    m_dict = noteLetter2IdxKeyInOctave("dict")
    m = m_dict[noteLetter]

    # Calculate number of half-steps from A4.
    k = 12*(n-4) + m

    # Apply any transposition.
    k += round(inst_transp_hsteps)

    # Convert into frequency.
    freq_Hz = refFreqA4_Hz * (2 ** (k/12 + c/1200))

    if includeExtraOutputs:
        outDict = {"freq":freq_Hz, "hsteps_from_A4":k, "octave_n":n, "hsteps_from_An":m, "cents":c}
        return outDict
    else:
        return freq_Hz


def freq2note(freq_Hz, refFreqA4_Hz=440, showCentsInName=True, showCentsWhitespace=True, includeNumericOutputs=False, use_flats=True, use_Esharp=False, use_Fb=False, use_Bsharp=False, use_Cb=False, inst_transp_hsteps=0, use_fancy_flat_sharp_chars=False):

    # If includeNumericOutputs is False, this function simply outputs
    # a string with the closest note name and (if showCentsInName is True)
    # the cents deviation from that note. Otherwise, this function
    # outputs a dictionary where note_name is that string,
    # hsteps_from_A4 is the number of half-steps away from A4,
    # octave_n is the octave number n, hsteps_from_An is the number
    # of half-steps away from An (A within the octave), and c is the
    # number of cents away from the true frequency of the named note.
    # Note name is reported at concert pitch (without transposition)
    # unless inst_transp_hsteps is nonzero. If inst_transp_hsteps is
    # nonzero, this function reports the written note played by the
    # instrument. inst_transp_hsteps is the (possibly negative)
    # integer number of half-steps that the instrument shifts notes
    # from concert pitch. So, for example, for a typical Western
    # Bb clarinet, inst_transp_hsteps would be -2.
    
    # k = Number of half-steps away from A4.
    # n = Octave number.
    # m = Number of half-steps away from A within octave.
    # k = 12(n-4) + m
    # c = Cents away from k.
    # freq_Hz = refFreqA4_Hz * (2 ** (k/12 + c/1200))

    p = log2(freq_Hz / refFreqA4_Hz)  # p = k/12 + c/1200
    p -= inst_transp_hsteps / 12  # Adjust for transposition.
    k = round(12*p)
    # inst_transp_hsteps is subtracted here, not added, when calculating p.
    # This is because we want to report the written note that the instrument
    # would need to play to match this frequency, which requires shifting the
    # concert-pitch note name in the opposite direction that the instrument
    # naturally shifts/transposes, to compensate for the instrument's shift.

    noteInfo = intParts2NoteName(hsteps_from_A4=k, use_flats=use_flats, use_Esharp=use_Esharp, use_Fb=use_Fb, use_Bsharp=use_Bsharp, use_Cb=use_Cb, includeExtraOutputs=True, use_fancy_flat_sharp_chars=use_fancy_flat_sharp_chars)
    noteName = noteInfo["note_name"]

    if showCentsInName or includeNumericOutputs:
        c = 1200 * (p - (k/12))  # p = k/12 + c/1200
        
    if showCentsInName:
        if c < 0:
            cSign = "-"
        else:
            cSign = "+"
        if showCentsWhitespace:
            cSign = " " + cSign + " "
            centsStr = " cents"
        else:
            centsStr = "cents"
        noteName = noteName + cSign + "{0:.1f}".format(abs(c)) + centsStr

    if includeNumericOutputs:
        outDict = {"note_name":noteName, "note_letter":noteInfo["note_letter"], "hsteps_from_A4":k, "octave_n":noteInfo["octave_n"], "hsteps_from_An":noteInfo["hsteps_from_An"], "cents":c}
        return outDict
    else:
        return noteName


def block_convert_freqs2notes(blockText, replaceFreqs=True, makeCombinedNoteLists=False, refFreqA4_Hz=440, showCentsInName=True, showCentsWhitespace=True, includeNumericOutputs=False, use_flats=True, use_Esharp=False, use_Fb=False, use_Bsharp=False, use_Cb=False, inst_transp_hsteps=0, use_fancy_flat_sharp_chars=False):

    # Convert note frequencies in Hz to their note names in a block of text.
    # When replaceFreqs is True (default), the note frequencies are replaced in
    # the text block. When replaceFreqs is False, the names of the notes on each
    # line of text are inserted into a new line underneath that line.
    # Notes on a line are assumed to be separated by commas, whitespace, or |.
    # The converter will ignore any text that comes after a % character
    # in each line. If makeCombinedNoteLists is True, the function will also
    # output a list of all note frequences and a list of all note names
    # found in the input blockText.
    # Other input parameters are described in the freq2note comments.

    # Split the text block into lines and keep the newline characters.
    blockTextLines = re.split("([\r\n])", blockText)

    linesWithNotes = []  # Will tell which lines have notes on them.
    linesToAdd = []

    if makeCombinedNoteLists:
        allFreqs = []
        allNoteNames = []

    # Process each line.
    for L in range(len(blockTextLines)):

        # Extract line, check for % sign, and prepare to ignore any text that follows a %.
        currentLine = blockTextLines[L].split("%")

        # Check whether any note frequencies are present on the current line. If yes, continue parsing this line.
        if re.search("[0-9]", currentLine[0]) is not None:

            linesWithNotes.append(L)
            freqList_strs = re.split("([,\\s\\|/])", currentLine[0])  # Split on whitespace, commas, |, and / characters.
            noteNamesList = []  # Initialize note name list.

            # Replace frequency with note name if next entry is a frequency (numeric). Otherwise leave it unchanged.
            for freq_str in freqList_strs:
                if re.search("[0-9]", freq_str) is not None:
                    freq = float(freq_str)
                    noteName = freq2note(freq, refFreqA4_Hz, showCentsInName, showCentsWhitespace, includeNumericOutputs, use_flats, use_Esharp, use_Fb, use_Bsharp, use_Cb, inst_transp_hsteps, use_fancy_flat_sharp_chars)
                    noteNamesList.append(noteName)
                    if makeCombinedNoteLists:
                        allFreqs.append(freq)
                        allNoteNames.append(noteName)
                else:
                    noteNamesList.append(freq_str)

            if replaceFreqs:
                currentLine[0] = "".join(noteNamesList)
                blockTextLines[L] = "%".join(currentLine)  # Rejoin with any comment at the end of the original line.
            else:
                linesToAdd.append(os_linesep + "".join(noteNamesList))  # No need to include an extra copy of the comment at the end of the to-be-appended line.

    # Append the note name lists if desired.
    if len(linesToAdd) > 0:
        nLinesAdded = 0
        while len(linesToAdd) > 0:
            lineToAdd = linesToAdd.pop(0)
            origLineIdx = linesWithNotes[nLinesAdded] + nLinesAdded  # blockTextLines is growing at each iteration, so the locations for inserting new lines must be accordingly shifted.
            blockTextLines.insert(origLineIdx+1, lineToAdd)
            nLinesAdded += 1

    # Rejoin the modified text block components.
    blockTextOut = "".join(blockTextLines)

    if makeCombinedNoteLists:
        return blockTextOut, allFreqs, allNoteNames
    else:
        return blockTextOut


def block_convert_notes2freqs(blockText, replaceFreqs=True, freqFormat=".4g", appendUnits=False, spaceBeforeUnits=False, makeCombinedNoteLists=False, refFreqA4_Hz=440, inst_transp_hsteps=0):

    # Convert note names to their frequencies in Hz in a block of text.
    # When replaceNoteNames is True (default), the note frequencies are replaced in
    # the text block. When replaceFreqs is False, the names of the notes on each
    # line of text are inserted into a new line underneath that line.
    # Notes on a line are assumed to be separated by commas, whitespace, or |.
    # The converter will ignore any text that comes after a % character
    # in each line. freqFormat is a Python format string specifying how to format each
    # frequency as a numeric string (default is ".4g", which is up to 4
    # significant figures). If appendUnits is True, then "Hz" will be
    # inserted after each frequency, with no spaces. If spaceBeforeUnits is True, then
    # " Hz" will be inserted after each frequency if appendUnits is also True.
    # spaceBeforeUnits has no effect if appendUnits is False.
    # If makeCombinedNoteLists is True, the function will also
    # output a list of all note frequences and a list of all note names
    # found in the input blockText.
    # Other input parameters are described in the note2freq comments.

    # Split the text block into lines and keep the newline characters.
    blockTextLines = re.split("([\r\n])", blockText)

    linesWithNotes = []  # Will tell which lines have notes on them.
    linesToAdd = []

    if makeCombinedNoteLists:
        allFreqs = []
        allNoteNames = []

    # Set up the string for converting frequency values into the desired format and
    # (if desired) appending units.
    formatterStr = "{0:" + freqFormat + "}"
    if appendUnits:
        if spaceBeforeUnits:
            formatterStr = formatterStr + " Hz"
        else:
            formatterStr = formatterStr + "Hz"

    # Process each line.
    for L in range(len(blockTextLines)):

        # Extract line, check for % sign, and prepare to ignore any text that follows a %.
        currentLine = blockTextLines[L].split("%")

        # Check whether any note names are present on the current line. If yes, continue parsing this line.
        if re.search("[a-gA-G][#b♯♭♮]?[+-]?[0-9]+", currentLine[0]) is not None:

            linesWithNotes.append(L)
            noteNamesList_strs = re.split("([a-gA-G][#b♯♭♮]?[+-]?[0-9]+)", currentLine[0])  # Split on main part of note names.
            freqsList_strs = []  # Initialize list of note frequency strings, which will include surrounding whitespace and commas.

            # Because a note name exists in this line and we split by note name base parts, the first item in noteNamesList_strs will not be a note name.
            # Keep this first string and leave it unchanged.
            leadingStr = noteNamesList_strs.pop(0)
            freqsList_strs.append(leadingStr)
            
            while len(noteNamesList_strs) > 0:
                noteMain = noteNamesList_strs.pop(0)
                centsPlusExtraText = noteNamesList_strs.pop(0)
                centsPlusExtraText = re.split("([,\\s\\|/]+$)", centsPlusExtraText)  # Separate the whitespace, commas, |, or / characters after the note from any cents deviation.
                noteNameFull = noteMain + centsPlusExtraText[0]  # Join note name main part and cents deviation.
                noteFreq = note2freq(noteNameFull, refFreqA4_Hz, inst_transp_hsteps=inst_transp_hsteps)  # Calculate frequency.
                if makeCombinedNoteLists:
                    allNoteNames.append(noteNameFull)
                    allFreqs.append(noteFreq)
                freqStr = formatterStr.format(noteFreq)  # Convert frequency into a string with desired format and (if desired) units.
                if len(centsPlusExtraText) > 1:
                    freqStr = freqStr + centsPlusExtraText[1]  # Add back the whitespace, commas, or | characters that were present after the note.
                freqsList_strs.append(freqStr)  # Add converted and processed note name with trailing characters to the list of frequency strings in the current line.
            
            if replaceFreqs:
                currentLine[0] = "".join(freqsList_strs)
                blockTextLines[L] = "%".join(currentLine)  # Rejoin with any comment at the end of the original line.
            else:
                linesToAdd.append(os_linesep + "".join(freqsList_strs))  # No need to include an extra copy of the comment at the end of the to-be-appended line.

    # Append the frequency lists if desired.
    if len(linesToAdd) > 0:
        nLinesAdded = 0
        while len(linesToAdd) > 0:
            lineToAdd = linesToAdd.pop(0)
            origLineIdx = linesWithNotes[nLinesAdded] + nLinesAdded  # blockTextLines is growing at each iteration, so the locations for inserting new lines must be accordingly shifted.
            blockTextLines.insert(origLineIdx+1, lineToAdd)
            nLinesAdded += 1

    # Rejoin the modified text block components.
    blockTextOut = "".join(blockTextLines)

    if makeCombinedNoteLists:
        return blockTextOut, allFreqs, allNoteNames
    else:
        return blockTextOut


def block_extract_note_name_letters_list(blockText):
    
    # Extract a list of the note names' letters in a block of text.
    # The extracted list is useful for guessing the associated key signature.
    # Notes on a line are assumed to be separated by commas, whitespace, or |.
    # The converter will ignore any text that comes after a % character
    # in each line.

    # Split the text block into lines and keep the newline characters.
    blockTextLines = re.split("([\r\n])", blockText)

    noteNameLetters = []  # Will append note name letters to this list as they are found.

    # Process each line.
    for L in range(len(blockTextLines)):

        # Extract line, check for % sign, and prepare to ignore any text that follows a %.
        currentLine = blockTextLines[L].split("%")

        # Split the line into parts that could be note names ("candidate" note names).
        candNoteNames = re.split("[,\\s\\|/]+", currentLine[0])

        # Check each candidate note name to see whether it is an actual note name
        # and add its letter part to the output list if so.
        for cnn in candNoteNames:
            if len(cnn) > 0 and (re.search("[a-gA-G]",cnn[0]) is not None):
                if len(cnn) > 1 and (cnn[1] in ["#","b","♯","♭"]):
                    noteNameLetters.append(cnn[0:2])
                else:
                    noteNameLetters.append(cnn[0])

    return noteNameLetters


def A4_freq_auto_est(note_freqs, A4_freq_init_guess=440, max_est_err_cents=1, A4_freq_half_range_cents=50, use_nested_grids=True):

    # Set up and perform a (potentially nested) grid search to automatically estimate which
    # A4 frequency "best fits" the given note_freqs. "Best fits" means "minimizes
    # the total absolute cents deviation between the given frequencies and their
    # nearest note under the choice of A4 frequency." Only consider A4 candidate frequencies
    # within a range of +/- A4_freq_half_range_cents (default = 50 cents,
    # 1 quarter-step, from the initial guess, because candidates spaced 1 or more
    # half-steps apart will be equally good fits because the cents deviation
    # loss/mismatch function is periodic).
    
    # Space the final candidates apart by at most max_est_err_cents so the final estimate falls
    # within that many cents of the "true" A4 frequency. Smaller values
    # of max_est_err_cents will give higher precision but make the search take longer.
    # If max_est_err_cents is small enough and use_nested_grids is True,
    # a nested/multi-tiered grid approach will be used,
    # where the first grid search will be done with larger spacing between candidates,
    # and then a finer grid search will be done in a smaller interval around the best
    # candidate from those first candidates, for increased efficiency.

    n_cands = ceil(2*A4_freq_half_range_cents / max_est_err_cents)
    
    if n_cands > 20 and use_nested_grids:
        # Use coarser starting grid and a nested/recursive approach.
        A4_freq_interim = A4_freq_auto_est(note_freqs, A4_freq_init_guess, max_est_err_cents*10, A4_freq_half_range_cents, True)
        A4_freq_best = A4_freq_auto_est(note_freqs, A4_freq_interim, max_est_err_cents, A4_freq_half_range_cents/10, True)

    else:
        cands_spacing_cents = 2*A4_freq_half_range_cents / n_cands
        cands_grid_cents = [(k+0.5)*cands_spacing_cents - A4_freq_half_range_cents for k in range(n_cands)]
        A4_freq_candidates = [A4_freq_init_guess * (2**(cands_grid_cents[k]/1200)) for k in range(n_cands)]
        A4_freq_best = A4_freq_grid_search(note_freqs, A4_freq_candidates)

    return A4_freq_best
    

def A4_freq_grid_search(note_freqs, A4_freq_candidates):
    
    # Find which candidate A4 frequency gives the lowest total absolute
    # deviation L between the given note frequencies in note_freqs
    # and their closest note names. This is an optimization problem
    # where we seek the A4 frequency that minimizes the loss
    # function L.

    loss = [sum([abs(freq2note(note_freq, refFreqA4_Hz=cand_A4_freq, includeNumericOutputs=True)["cents"]) for note_freq in note_freqs]) for cand_A4_freq in A4_freq_candidates]
    loss_min = min(loss)
    A4_freq_best = A4_freq_candidates[loss.index(loss_min)]
    
    return A4_freq_best


def key_sig_guess(note_names, verbose_output=False, names_already_preproc=False, output_fancy_flat_sharp_chars=False):

    # Guess which major key signature best fits a list of note
    # name strings via a similarity-scoring system. Output is a string by default.
    # However, verbose_output=True to also report the similarity scores
    # for every key signature and other potentially useful outputs in dict format.
    # Set names_already_preproc=True to skip steps if note_names is already a list
    # of trimmed note names with no octave numbers, no cents deviations,
    # no fancy flat and sharp characters (only b or #, not fancy ♭ or ♯), and
    # the first character uppercase (e.g., "Ab", not "ab", for A-flat).
    
    # For every note in note_names that also appears in some key signature,
    # 1 point will be added to the similarity/match score for
    # that key signature.  The key signature with the highest match score
    # will be the guessed one.  When there is a tie, the key signature
    # with the smallest number of sharps or flats will be guessed, with
    # the flat key signature winning if there is still a tie by those criteria.

    # Make list of key signatures and the notes they contain.
    key_sigs = ["C", "F", "G", "Bb", "D", "Eb", "A", "Ab", "E", "Db/C#", "B/Cb", "Gb/F#"]  # Sort by number of flats and sharps, with flat keys listed first, to facilitate tie-breaking in the order described above.
    notes_in_each_sig = { "C": "A B C D E F G Cb B# Fb E#".split() }  # Include alternate note names so those notes still contribute to the match scores.
    notes_in_each_sig["F"] = "A Bb C D E F G A# B# Fb E#".split()
    notes_in_each_sig["Bb"] = "A Bb C D Eb F G A# B# D# E#".split()
    notes_in_each_sig["Eb"] = "Ab Bb C D Eb F G G# A# B# D# E#".split()
    notes_in_each_sig["Ab"] = "Ab Bb C Db Eb F G G# A# B# C# D# E#".split()
    notes_in_each_sig["Db/C#"] = "Ab Bb C Db Eb F Gb G# A# B# C# D# E# F#".split()
    notes_in_each_sig["Gb/F#"] = "Ab Bb Cb Db Eb F Gb G# A# B C# D# E# F#".split()
    notes_in_each_sig["G"] = "A B C D E F# G Cb B# Fb".split()
    notes_in_each_sig["D"] = "A B C# D E F# G Cb Db Fb Gb".split()
    notes_in_each_sig["A"] = "A B C# D E F# G# Cb Db Fb Gb Ab".split()
    notes_in_each_sig["E"] = "A B C# D# E F# G# Cb Db Eb Fb Gb Ab".split()
    notes_in_each_sig["B/Cb"] = "A# B C# D# E F# G# Bb Cb Db Eb Fb Gb Ab".split()

    # Preprocess note names if necessary.
    if names_already_preproc:
        note_names_preproc = note_names
    else:
        note_names_preproc = []
        for note in note_names:
            if len(note) == 1:
                note_names_preproc.append(note.upper())
            elif len(note) > 1:
                if note[1] == "b" or note[1] == "#":
                    note_names_preproc.append(note[0].upper() + note[1])
                elif note[1] == "♭":
                    note_names_preproc.append(note[0].upper() + "b")
                elif note[1] == "♯":
                    note_names_preproc.append(note[0].upper() + "#")
                else:
                    note_names_preproc.append(note[0].upper())

    # Calculate similarity/match score for each key signature.
    key_sig_scores = []
    for k in range(len(key_sigs)):
        key_sig_scores.append(sum([int(note in notes_in_each_sig[key_sigs[k]]) for note in note_names_preproc]))

    # Identify the winning key signature (the one with highest match score that also, if there is a tie, appears first in the key signatures list).
    key_sig_guess = key_sigs[key_sig_scores.index(max(key_sig_scores))]

    # Replace simple flat and sharp characters with fancier versions if desired.
    if output_fancy_flat_sharp_chars:
        key_sig_guess = "♭".join(key_sig_guess.split("b"))
        key_sig_guess = "♯".join(key_sig_guess.split("#"))

    # Report result and include extra info if desired.
    if verbose_output:
        output_info = {"guess":key_sig_guess, "key_sigs":key_sigs, "scores":key_sig_scores, "note_names_preproc":note_names_preproc}
        return output_info
    else:
        return key_sig_guess

    
def intParts2NoteName(hsteps_from_A4, octave_n=None, hsteps_from_An=None, use_flats=True, use_Esharp=False, use_Fb=False, use_Bsharp=False, use_Cb=False, includeExtraOutputs=False, use_fancy_flat_sharp_chars=False):

    # Return the name of the note that is k half-steps from A4,
    # where k = hsteps_from_A4, without transposition.
    # If you already know which octave
    # the note is in (octave_n) and how many half-steps the note
    # is from the A within that octave (hsteps_from_An), then
    # set hsteps_from_A4 to None to avoid recalculating
    # octave_n and hsteps_from_An.  use_Esharp and use_Bsharp
    # have no effect if use_flats is True.  use_Fb and use_Cb
    # have no effect if use_flats is False.  So use_flats has
    # a "stronger" effect/precedence than the other use_...
    # enharmonic settings.

    # If includeExtraOutputs is False (default), then
    # only the note name string is returned.
    # If includeExtraOutputs is True, then the output is a
    # dictionary called outDict, where:
    # outDict["note_name"] = the note name string (for example: "B2", "Eb-1", or "F#7")
    # outDict["note_letter"] = the letter(s) part of the note name string (for example: "B", "Eb", or "F#")
    # outDict["hsteps_from_A4"] = hsteps_from_A4 (an integer)
    # outDict["octave_n"] = octave_n (an integer)
    # outDict["hsteps_from_An"] = hsteps_from_An (an integer)

    # k = Number of half-steps away from A4.
    # n = Octave number.
    # m = Number of half-steps away from A within octave.
    # k = 12(n-4) + m
    # c = Cents away from k.
    # freq_Hz = refFreqA4_Hz * (2 ** (k/12 + c/1200))

    if hsteps_from_A4 is None:
        n = octave_n
        m = hsteps_from_An
        if includeExtraOutputs:
            k = 12*(n-4) + m  # Must calculate k in this case because it will be reported in the extra outputs.

    else:
        k = hsteps_from_A4

        # Modulus m' for division by 12 will run from 0 to 11,
        # but m note index runs from -9 to 2 for note names other than
        # B# and Cb, and therefore m is a shifted modulus.
        # B# and Cb are handled later as special cases if the user
        # wants to use them.
        # m = m' - 9.
        # k = 12(n-4) + m'-9
        # k+9 = 12(n-4) + m'
        # (n-4) = (k+9) // 12 = floor((k+9)/12)
        # m' = (k+9) % 12
        n = ((k+9) // 12) + 4  # (n-4) + 4
        m = ((k+9) % 12) - 9  # m' - 9

    # These 2 lines of code and the noteLetter2IdxKeyInOctave
    # function are configured to always return sharp names
    # for non-natural notes (black keys on a piano) and never to
    # return E#, Fb, B#, or Cb:
    m_key_names, m_key_idx = noteLetter2IdxKeyInOctave("lists")
    noteLetter = m_key_names[m_key_idx.index(m)]

    # Adjust note name according to user preferences. If converting to
    # B# or Cb, also adjust m and n accordingly.
    if use_flats:
        if "#" in noteLetter:
            noteLetter = m_key_names[m_key_idx.index(m)+1]
        else:
            if use_Fb and (noteLetter == "E"):
                noteLetter = "Fb"
            if use_Cb and (noteLetter == "B"):
                noteLetter = "Cb"
                m = -10
                n = n+1
    else:
        if use_Esharp and (noteLetter == "F"):
            noteLetter = "E#"
        if use_Bsharp and (noteLetter == "C"):
            noteLetter = "B#"
            m = 3
            n = n-1
            
    noteName = noteLetter + "{0:d}".format(n)

    if use_fancy_flat_sharp_chars:
        noteName = "♭".join(noteName.split("b"))
        noteName = "♯".join(noteName.split("#"))

    if includeExtraOutputs:
        outDict = {"note_name":noteName, "note_letter":noteLetter, "hsteps_from_A4":k, "octave_n":n, "hsteps_from_An":m}
        return outDict
    else:
        return noteName
        

def calc_inst_transp_hsteps(target_inst_key, transp_down=True, extra_octave_shift=0):

    # Calculate inst_transp_hsteps: the number of half-steps by which a "target instrument"
    # (in a "target key") "shifts" its written notes relative to those
    # same-named notes' concert pitch. target_inst_key is a string indicating
    # the key of the target instrument (such as "Bb" for the current Western
    # Bb clarinet), and transp_down is True or False and
    # tells whether the instrument shifts upward or downward.
    # extra_octave_shift is an integer indicating how many octaves
    # the instrument shifts after the within-octave part of the transposition.
    #
    # The key of the instrument (target_inst_key) is the concert-pitch note letter
    # that sounds when the player fingers a written C on the instrument.
    #
    # Examples:
    #
    # The current Western Bb clarinet sounds a concert-pitch Bb when
    # the player fingers the written C just above that Bb.
    # This instrument corresponds to target_inst_key="Bb",
    # transp_down=True, and extra_octave_shift=0, which yields inst_transp_hsteps = -2.
    # In this sense, the Western Bb clarinet "shifts a written C down
    # 2 half steps to sound like a concert-pitch Bb" and more generally
    # "shifts written notes down 2 half steps".
    #
    # A Bb tenor saxophone sounds a concert-pitch Bb that is one octave
    # and one whole step (2 half steps) below the written C when the player
    # fingers that written C.  For this instrument, target_inst_key="Bb",
    # transp_down=True, and extra_octave_shift = -1, which yields
    # inst_transp_hsteps = -14 (-2 for the within-octave shift and -12
    # for the following full-octave shift).
    #
    # An Eb sopranino clarinet sounds a concert-pitch Eb three half steps
    # above the written C that a player fingers.  For this instrument,
    # target_inst_key="Eb", transp_down=False, and extra_octave_shift=0,
    # which yields inst_transp_hsteps = 3.


    # Trim any whitespace and ensure that the target key uses uppercase first letter.
    target_inst_key_preproc = target_inst_key.strip()
    target_inst_key_preproc = target_inst_key_preproc.title()

    # Simplify Cb or B#.
    if target_inst_key_preproc == "Cb":
        target_inst_key_preproc = "B"
    elif target_inst_key_preproc == "B#":
        target_inst_key_preproc = "C"

    # Convert target key note letter into number m within octave.
    m_dict = noteLetter2IdxKeyInOctave("dict")
    m_target = m_dict[target_inst_key_preproc]
    m_starting = m_dict["C"]  # Get m for concert pitch (key of C).

    # Calculate initial guess of shift.
    inst_transp_hsteps = m_target - m_starting

    if transp_down:  # Transposing down.
        if inst_transp_hsteps > 0:
            inst_transp_hsteps -= 12  # Needed to transpose down instead, so shift down 1 octave.
        inst_transp_hsteps -= 12*extra_octave_shift  # Apply any extra octave shift.

    else:  # Transposing up.
        if inst_transp_hsteps < 0:
            inst_transp_hsteps += 12  # Needed to transpose up instead, so shift up 1 octave.
        inst_transp_hsteps += 12*extra_octave_shift  # Apply any extra octave shift.

    return inst_transp_hsteps


def inst_transp_info_dict(calc_transp_hsteps=True):

    # Output a dictionary with transposition information for several predefined instruments.
    # Format will be: {"instrument 1 name" : {"key":"key as string", "transp_down":True/False, "extra_octave_shift":nonnegative integer, "inst_transp_hsteps":integer if computed}, ...}
    # Example with calc_transp_hsteps=True: {"Tenor Saxophone" : {"key":"Bb", "transp_down":True, "extra_octave_shift":1, "inst_transp_hsteps":-14}, ...}
    # Example with calc_transp_hsteps=False: {"Clarinet in A" : {"key":"A", "transp_down":True, "extra_octave_shift":0}, ...}

    # Initialize the output dictionary with an option for concert pitch.
    outDict = {"None / Concert Pitch" : {"key":"C", "transp_down":True, "extra_octave_shift":0}}  # transp_down would have no effect in this case (key of C with no extra octave shifts).

    # Add transposition info for each desired instrument.
    outDict["Alto Clarinet in Eb"] = {"key":"Eb", "transp_down":True, "extra_octave_shift":0}
    outDict["Alto Flute"] = {"key":"G", "transp_down":True, "extra_octave_shift":0}
    outDict["Alto Saxophone"] = {"key":"Eb", "transp_down":True, "extra_octave_shift":0}
    outDict["Baritone Saxophone"] = {"key":"Eb", "transp_down":True, "extra_octave_shift":1}
    outDict["Bass Clarinet in Bb"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":1}
    outDict["Bass Flute"] = {"key":"C", "transp_down":True, "extra_octave_shift":1}
    outDict["Bassoon"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Clarinet in A"] = {"key":"A", "transp_down":True, "extra_octave_shift":0}
    outDict["Clarinet in Bb"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":0}
    outDict["Clarinet in Eb"] = {"key":"Eb", "transp_down":False, "extra_octave_shift":0}
    outDict["Contrabass (String)"] = {"key":"C", "transp_down":True, "extra_octave_shift":1}
    outDict["Contrabass Flute"] = {"key":"C", "transp_down":True, "extra_octave_shift":2}
    outDict["Contrabassoon"] = {"key":"C", "transp_down":True, "extra_octave_shift":1}
    outDict["English Horn"] = {"key":"F", "transp_down":True, "extra_octave_shift":0}
    outDict["Euphonium (Treble Clef)"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":2}
    outDict["Flute"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["French Horn"] = {"key":"F", "transp_down":True, "extra_octave_shift":0}
    outDict["Glockenspiel"] = {"key":"C", "transp_down":False, "extra_octave_shift":2}
    outDict["Marimba"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Oboe"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Piano"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Piccolo in C"] = {"key":"C", "transp_down":False, "extra_octave_shift":1}
    outDict["Piccolo in Db"] = {"key":"Db", "transp_down":False, "extra_octave_shift":1}
    outDict["Soprano Saxophone"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":0}
    outDict["Tenor Saxophone"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":1}
    outDict["Trombone"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Trumpet in Bb"] = {"key":"Bb", "transp_down":True, "extra_octave_shift":0}
    outDict["Tuba"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Violin"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Viola"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Violoncello"] = {"key":"C", "transp_down":True, "extra_octave_shift":0}
    outDict["Xylophone"] = {"key":"C", "transp_down":False, "extra_octave_shift":1}

    if calc_transp_hsteps:
        for inst_name in outDict.keys():
            transp_info = outDict[inst_name]
            outDict[inst_name]["inst_transp_hsteps"] = calc_inst_transp_hsteps(transp_info["key"], transp_info["transp_down"], transp_info["extra_octave_shift"])

    return outDict


