## Program Description
#
# Author: Zachary Markow
# Written 27 March 2024.
# Last Updated 26 May 2024.
#
# Run the GUI for the author's freq2notename tools when the
# user runs python3 -m freq2notename.  Code is identical
# to freq2notename_dashboard.py.
#


## Imports
import freq2notename_utils as f2nn
import tkinter as tk
import tkinter.ttk as ttk
#from tkinter import font


# Define instrument list for transposition settings.
inst_transp_info_dict = f2nn.inst_transp_info_dict()
instsForTransp = [inst_name for inst_name in inst_transp_info_dict.keys()]
instsForTransp.insert(1, "Other / Custom")  # Add a custom option as the second "instrument" in the list.


# Callback functions for user interface events.

def A4AutoEstBtnClick():

    # Clear any text selection highlight in the A4 frequency box.
    A4Box.selection_clear()
    
    # Estimate A4 frequency automatically from the frequency text block.
    freqBlockText = inputBox.get("1.0", "end")  # Get full text.

    # Run block conversion function only to get the parsed list of frequencies.
    try:
        blockTextOut, allFreqs, allNoteNames = f2nn.block_convert_freqs2notes(freqBlockText, makeCombinedNoteLists=True)
    except:
        allFreqs = []
        statusMsg.set("Status: Error occurred while reading or converting text with frequencies.")

    if len(allFreqs) > 0:
        try:
            A4_freq_best = f2nn.A4_freq_auto_est(allFreqs)  # Estimate A4 frequency from the frequency list if any frequencies were found.
        except:
            statusMsg.set("Status: Error occurred while auto-estimating A4 frequency.")
            return  # Do not proceed.
        else:
            A4FreqStr.set("{0:.5g}".format(A4_freq_best))  # Format and display the best-fitting A4 frequency in the A4 entry box.
            A4BoxFocusOut()  # Trigger checks that decide whether to warn user that A4 frequency changed.
    else:
        statusMsg.set("Status: No frequencies found for auto-estimating A4 frequency.")

    return


def keyGuessBtnClick():
    # Guess the key signature from the note name main parts in the note name text block.
    nnBlockText = outputBox.get("1.0", "end")  # Get full text.

    # Extract the note name letters.
    try:
        nnLetters = f2nn.block_extract_note_name_letters_list(nnBlockText)
    except:
        statusMsg.set("Status: Error occurred while reading text with note names.")
        return  # Do not proceed.

    if len(nnLetters) > 0:
        try:
            key_sig_guess = f2nn.key_sig_guess(nnLetters, output_fancy_flat_sharp_chars=prefFancyChars.get())  # Guess key signature from the note names if any note names were found.
        except:
            statusMsg.set("Status: Error occurred while guessing key signature.")
        else:
            keyGuess.set(key_sig_guess)  # Display the guessed key signature in the user interface.
            statusMsg.set("Status: Key signature guessed.")
    else:
        statusMsg.set("Status: No notes found for key signature guess.")

    return


def convBtnClick():

    key_guess_failed = False  # Assume that any key signature guess is successful unless/until one fails.

    if convDirIsF2NN.get():  # Frequency to note name conversion.

        freqBlockText = inputBox.get("1.0", "end")  # Get full text block from frequencies box.

        # Check for valid A4 frequency. If not valid, auto-estimate it.
        try:
            A4FreqFloat = float(A4FreqStr.get())
        except:
            A4AutoEstBtnClick()
            try:
                A4FreqFloat = float(A4FreqStr.get())
            except:
                statusMsg.set("Status: Invalid A4 frequency specified and error occurred while reading or converting text with frequencies.")
                return  # Do not proceed.

        # If any enharmonic settings are "Auto", convert the frequencies
        # into a list of note names and guess the key signature first.
        # Then change the enharmonic labeling settings accordingly.

        enharmPrefs = [overallEnharmPref.get(), useFbMenuVal.get(), useCbMenuVal.get(), useBsharpMenuVal.get(), useEsharpMenuVal.get()]
        if "Auto" in enharmPrefs:
            try:
                nnBlockText, freqList, noteNameList = f2nn.block_convert_freqs2notes(freqBlockText, makeCombinedNoteLists=True, refFreqA4_Hz=A4FreqFloat, inst_transp_hsteps=read_transpFinalShiftStr())
            except:
                statusMsg.set("Status: Error occurred while reading or converting text with frequencies.")
                return  # Do not proceed.
            if len(noteNameList) > 0:
                try:
                    key_sig_guess = f2nn.key_sig_guess(noteNameList)  # To simplify key signature-based decisions, use simple b and # for flats and sharps in key signature regardless of user preference here.
                except:
                    key_guess_failed = True
                    key_sig_guess = ""
                else:
                    keyGuess.set(key_sig_guess)
            else:
                key_sig_guess = ""

        # Overall enharmonic preference.
        if enharmPrefs[0] == "Flats" or enharmPrefs[0] == "Sharps":
            use_flats_now = (enharmPrefs[0] == "Flats")
        else:  # Auto mode for overall use of flats or sharps.
            if key_sig_guess in ["F","Bb","Eb","Ab"]:  # Key has 1-4 flats. Use flats.
                use_flats_now = True
            elif key_sig_guess in ["G","D","A","E"]:  # Key has 1-4 sharps. Use sharps.
                use_flats_now = False
            else:  # Key has 0 or 5-7 flats or sharps.
                # Calculate a "flats preference" score based on the "natural enharmonic" preferences.
                natEnharmPrefs_flats = enharmPrefs[1:3]
                natEnharmPrefs_sharps = enharmPrefs[3:]
                flats_pref_score = 0
                for pb in natEnharmPrefs_flats:
                    if pb == "Yes":
                        flats_pref_score += 1
                    elif pb == "No":
                        flats_pref_score -= 1
                for ps in natEnharmPrefs_sharps:
                    if ps == "Yes":
                        flats_pref_score -= 1
                    elif ps == "No":
                        flats_pref_score += 1
                # Decide based on flats preference score.
                if flats_pref_score > 0:
                    use_flats_now = True
                elif flats_pref_score < 0:
                    use_flats_now = False
                else:
                    # Break tie by choosing the key signature with the fewest sharps or flats.
                    # For the Gb/F# key signature, which has an equal number of flats and sharps (6), default to flats.
                    if key_sig_guess == "B/Cb":
                        use_flats_now = False  # 5 sharps vs. 7 flats
                    else:
                        use_flats_now = True

        # Fb preference.
        if enharmPrefs[1] == "Yes" or enharmPrefs[1] == "No":
            use_Fb_now = enharmPrefs[1] == "Yes"
        else:  # Auto mode.
            use_Fb_now = key_sig_guess == "B/Cb" and use_flats_now

        # Cb preference.
        if enharmPrefs[2] == "Yes" or enharmPrefs[2] == "No":
            use_Cb_now = enharmPrefs[2] == "Yes"
        else:  # Auto mode.
            use_Cb_now = (key_sig_guess in ["Gb/F#","B/Cb"]) and use_flats_now

        # B# preference.
        if enharmPrefs[3] == "Yes" or enharmPrefs[3] == "No":
            use_Bsharp_now = enharmPrefs[3] == "Yes"
        else:  # Auto mode.
            use_Bsharp_now = key_sig_guess == "Db/C#" and not use_flats_now

        # E# preference.
        if enharmPrefs[4] == "Yes" or enharmPrefs[4] == "No":
            use_Esharp_now = enharmPrefs[4] == "Yes"
        else:  # Auto mode.
            use_Esharp_now = (key_sig_guess in ["Db/C#","Gb/F#"]) and not use_flats_now

        # Convert frequencies to notes with full preference set.
        try:
            nnBlockText, freqList, noteNameList = f2nn.block_convert_freqs2notes(freqBlockText, replaceFreqs=replaceConvItems.get(), makeCombinedNoteLists=True, refFreqA4_Hz=A4FreqFloat, showCentsInName=centsDevCBOn.get(), showCentsWhitespace=False, use_flats=use_flats_now, use_Esharp=use_Esharp_now, use_Fb=use_Fb_now, use_Bsharp=use_Bsharp_now, use_Cb=use_Cb_now, inst_transp_hsteps=read_transpFinalShiftStr(), use_fancy_flat_sharp_chars=prefFancyChars.get())
        except:
            statusMsg.set("Status: Error occurred while reading or converting text with frequencies.")
            return  # Do not proceed.

        # Replace note names text box contents with the converted block text.
        #outputBox.delete("1.0", "end")
        #outputBox.insert("1.0", nnBlockText)
        outputBox.replace("1.0", "end", nnBlockText)

        # Record the A4 frequency used during this conversion for change detection later.
        A4FreqStrLastConv.set(A4FreqStr.get())

        # Update guessed key signature.
        if len(noteNameList) > 0:
            try:
                key_sig_guess = f2nn.key_sig_guess(noteNameList, output_fancy_flat_sharp_chars=prefFancyChars.get())  # Now consider user preference for displaying the key signature.
            except:
                key_guess_failed = True
            else:
                keyGuess.set(key_sig_guess)


    else:  # Note name to frequency conversion.

        nnBlockText = outputBox.get("1.0", "end")  # Get full text block from note names box.

        # Check for valid A4 frequency. If not valid, set it to 440 Hz.
        try:
            A4FreqFloat = float(A4FreqStr.get())
        except:
            A4FreqStr.set("440")
            A4FreqFloat = 440.0

        # Convert notes to frequencies.
        try:
            freqBlockText, freqList, noteNameList = f2nn.block_convert_notes2freqs(nnBlockText, replaceFreqs=replaceConvItems.get(), makeCombinedNoteLists=True, refFreqA4_Hz=A4FreqFloat, inst_transp_hsteps=read_transpFinalShiftStr())
        except:
            statusMsg.set("Status: Error occurred while reading or converting text with note names.")
            return  # Do not proceed.

        # Replace frequencies text box contents with the converted block text.
        #inputBox.delete("1.0", "end")
        #inputBox.insert("1.0", freqBlockText)
        inputBox.replace("1.0", "end", freqBlockText)

        # Record the A4 frequency used during this conversion for change detection later.
        A4FreqStrLastConv.set(A4FreqStr.get())

        # Update guessed key signature.
        if len(noteNameList) > 0:
            try:
                key_sig_guess = f2nn.key_sig_guess(noteNameList)
            except:
                key_guess_failed = True
            else:
                keyGuess.set(key_sig_guess)

    
    # Set flag indicating that at least one conversion has been done.
    if not firstConvDone.get():
        firstConvDone.set(True)

    # Mark both text boxes as unmodified so that the next change triggers a <<Modified>> event from them.
    inputBox.edit_modified(False)
    outputBox.edit_modified(False)

    # Unhighlight text boxes.
    #resetTextBoxBGColors()

    # Update status message.
    if key_guess_failed:
        statusMsg.set("Status: Conversion completed, but key signature guess failed.")
    else:
        statusMsg.set("Status: Conversion completed. Ready for further operations.")

    return


def showDetSetsBtnClick():
    # Toggle whether detailed settings are visible.
    if showDetSetsBtnText.get()[0:4] == "Show":  # Detailed settings were not visible, so show them and change the button text so the next button click would hide them.
        detSetsFrame.grid()
        showDetSetsBtnText.set("Hide Detailed Settings")
    else:  # Detailed settings were visible, so show them and change the button text so the next button click would show them.
        detSetsFrame.grid_remove()
        showDetSetsBtnText.set("Show Detailed Settings")
    return


def restoreDefaultDetSetsBtnClick():
    
    # Restore default values of detailed settings.
    centsDevCBOn.set(False)
    overallEnharmPref.set("Auto")
    useBsharpMenuVal.set("Auto")
    useCbMenuVal.set("Auto")
    useEsharpMenuVal.set("Auto")
    useFbMenuVal.set("Auto")
    prefFancyChars.set(False)
    instSel.set("None / Concert Pitch")

    instOctBox.selection_clear()  # Clear any text selection highlight in the extra octave shift box.
    
    return


def A4BoxFocusOut(ev=None):
    # Check whether the A4 frequency in the box has changed.
    # Warn the user if it has changed unless no conversions have been done yet (in which case A4FreqStrLastConv is the empty string "".
    if len(A4FreqStrLastConv.get()) > 0 and A4FreqStr.get() != A4FreqStrLastConv.get():
        statusMsg.set("Status: Some items have been modified since the last conversion.")
    return


def resetTextBoxBGColors():
    inputBox["background"] = "white"
    outputBox["background"] = "white"
    return


def warnIfInputBoxModF2T(*args):
    # Designed to be called if text box fires a <<Modified>> event, which means its modified flag has changed.
    # If the change is from True to False, then the modified flag was simply being reset, so do nothing.
    # If the change is from False to True, then check whether the user should be notified.
    if inputBox.edit_modified():
        warnChangesSinceLastConv()
    return


def warnIfOutputBoxModF2T(*args):
    # Designed to be called if text box fires a <<Modified>> event, which means its modified flag has changed.
    # If the change is from True to False, then the modified flag was simply being reset, so do nothing.
    # If the change is from False to True, then check whether the user should be notified.
    if outputBox.edit_modified():
        warnChangesSinceLastConv()
    return
    

def warnChangesSinceLastConv(*args):
    if firstConvDone.get():
        statusMsg.set("Status: Some items have been modified since the last conversion.")
    return


def instSelPossibleChange(*args):
    instOctBox.selection_clear()  # Clear any text selection highlight in the extra octave shift box.
    warnChangesSinceLastConv()  # Check whether to warn the user about possible changes.
    
    inst_name = instSel.get()

    if inst_name == "Other / Custom":
        # Enable the custom transposition setting widgets for the user.
        instKeyMenu.state(["!disabled"])
        transpDirMenu.state(["!disabled"])
        instOctBox.state(["!disabled"])

    else:
        # Disable the custom transposition setting widgets for the user because they will be set automatically.
        instKeyMenu.state(["disabled"])
        transpDirMenu.state(["disabled"])
        instOctBox.state(["disabled"])

        # Auto-populate the custom transposition settings based on the instrument name.
        inst_transp_info = inst_transp_info_dict[inst_name]
        instKey.set(inst_transp_info["key"])
        instOctShiftStr.set(inst_transp_info["extra_octave_shift"])
        if inst_transp_info["transp_down"]:
            transpDirStr.set("Down")
        else:
            transpDirStr.set("Up")
        transpFinalShiftStr.set("{0:d}".format(inst_transp_info["inst_transp_hsteps"]))
        
    return


def instTranspCustomSettingsChange(*args):
    
    # Recalculate number of half-steps the instrument transposes
    # if using a custom instrument and the user has changed its
    # key, transposition direction, or number of extra octave shifts.
    if instSel.get() == "Other / Custom":
        warnChangesSinceLastConv()
        octShift = read_instOctShiftStr()
        transpFinalShift = f2nn.calc_inst_transp_hsteps(instKey.get(), transpDirStr.get()=="Down", octShift)
        transpFinalShiftStr.set("{0:d}".format(transpFinalShift))
    
    return


def transpFinalShiftStrChange(*args):
    # Update the text that displays the final transposition shift to the user.
    transpFinalShiftLabelStr.set("Half-steps inst sounds above written pitch: {0:d}".format(read_transpFinalShiftStr()))
    return


def read_instOctShiftStr():
    # Get value of instOctShiftStr but return 0 in cases where the user has provided invalid input.
    # Needed to handle situations where user has deleted content of instOctBox while not finished editing it.
    try:
        octShift = int(instOctShiftStr.get())
    except ValueError:
        octShift = 0
    return octShift


def read_transpFinalShiftStr():
    # Get value of transpFinalShiftStr but return 0 in cases where the value is invalid.
    # Needed to handle situations where user has deleted content of instOctBox while not finished editing it.
    try:
        finalShift = int(transpFinalShiftStr.get())
    except ValueError:
        finalShift = 0
    return finalShift


def deselReadOnlyCBText(ev=None):
    # Deselect text inside a read-only combobox where the user has just made a selection.
    ev.widget.selection_clear()
    return


# Create root app and outermost frame.
root = tk.Tk()
root.title("freq2notename Dashboard")
outermostFrame = ttk.Frame(root)
outermostFrame.grid(column=0, row=0, sticky="nwes")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)


# Outermost frame will have 3 sub-frames stacked vertically (3 rows x 1 column grid).
# Most area should be devoted to the input and output text boxes.
outermostFrame.columnconfigure(0, weight=10)
outermostFrame.rowconfigure(0, weight=15)
outermostFrame.rowconfigure(1, weight=0)
outermostFrame.rowconfigure(2, weight=1)
#outermostFrame.rowconfigure(3, weight=1)


# Set a constant for adjusting the left and right overall padding.
padx_master = 15


# Create top section (sub-frame) with labeled input and output text boxes.

# Set constants for initial main text box frame dimensions.
mainBoxInitWidth = 60
mainBoxInitHeight = 15

# This sub-frame will be a 2x2 grid with labels in the top row and text box+scrollbar frames in the bottom row.
inOutFrame = ttk.Frame(outermostFrame)
inOutFrame.grid(column=0, row=0, sticky="nwes")
inputBoxLabel = ttk.Label(inOutFrame, text="Text with frequencies in Hz")
inputBoxLabel.grid(column=0, row=0, sticky="s", padx=(padx_master,5), pady=(5,0))
outputBoxLabel = ttk.Label(inOutFrame, text="Text with note names written for instrument")
outputBoxLabel.grid(column=1, row=0, sticky="s", padx=(5,padx_master), pady=(5,0))
inBoxAndSBarFrame = ttk.Frame(inOutFrame)
inBoxAndSBarFrame.grid(column=0, row=1, sticky="nwes", padx=(padx_master,5), pady=(5,0))
outBoxAndSBarFrame = ttk.Frame(inOutFrame)
outBoxAndSBarFrame.grid(column=1, row=1, sticky="nwes", padx=(5,padx_master), pady=(5,0))
inOutFrame.columnconfigure(0, weight=1)
inOutFrame.columnconfigure(1, weight=1)
inOutFrame.rowconfigure(0, weight=1, minsize=20)
inOutFrame.rowconfigure(1, weight=9, minsize=20)

# Input text box frame will be a 2x2 grid with the box, a horizontal scrollbar, and a vertical scrollbar.
inputBox = tk.Text(inBoxAndSBarFrame, width=mainBoxInitWidth, height=mainBoxInitHeight)
inputBox.grid(column=0, row=0, sticky="nwes")
inputBox.bind("<<Modified>>", warnIfInputBoxModF2T)
inputSBarV = ttk.Scrollbar(inBoxAndSBarFrame, orient=tk.VERTICAL, command=inputBox.yview)
inputSBarV.grid(column=1, row=0, sticky="nws")
inputBox["yscrollcommand"] = inputSBarV.set
inputSBarH = ttk.Scrollbar(inBoxAndSBarFrame, orient=tk.HORIZONTAL, command=inputBox.xview)
inputSBarH.grid(column=0, row=1, sticky="nwe")
inputBox["xscrollcommand"] = inputSBarH.set
inBoxAndSBarFrame.columnconfigure(0, weight=9, minsize=20)
inBoxAndSBarFrame.columnconfigure(1, weight=1, minsize=20)
inBoxAndSBarFrame.rowconfigure(0, weight=9, minsize=20)
inBoxAndSBarFrame.rowconfigure(1, weight=1, minsize=20)

# Output text box frame will be a 2x2 grid with the box, a horizontal scrollbar, and a vertical scrollbar.
outputBox = tk.Text(outBoxAndSBarFrame, width=mainBoxInitWidth, height=mainBoxInitHeight)
outputBox.grid(column=0, row=0, sticky="nwes")
outputBox.bind("<<Modified>>", warnIfOutputBoxModF2T)
outputSBarV = ttk.Scrollbar(outBoxAndSBarFrame, orient=tk.VERTICAL, command=outputBox.yview)
outputSBarV.grid(column=1, row=0, sticky="nws")
outputBox["yscrollcommand"] = outputSBarV.set
outputSBarH = ttk.Scrollbar(outBoxAndSBarFrame, orient=tk.HORIZONTAL, command=outputBox.xview)
outputSBarH.grid(column=0, row=1, sticky="nwe")
outputBox["xscrollcommand"] = outputSBarH.set
outBoxAndSBarFrame.columnconfigure(0, weight=9, minsize=20)
outBoxAndSBarFrame.columnconfigure(1, weight=1, minsize=20)
outBoxAndSBarFrame.rowconfigure(0, weight=9, minsize=20)
outBoxAndSBarFrame.rowconfigure(1, weight=1, minsize=20)


# Create second section (sub-frame) with A4 frequency, key signature guess, and status message widgets.
# This section will be a 3x2 grid.

A4KeyStatusFrame = ttk.Frame(outermostFrame)
A4KeyStatusFrame.grid(column=0, row=1, sticky="nwes")
A4KeyStatusFrame.columnconfigure(0, weight=1)
A4KeyStatusFrame.columnconfigure(1, weight=1)
A4KeyStatusFrame.rowconfigure(0, weight=1)
A4KeyStatusFrame.rowconfigure(1, weight=1)
A4KeyStatusFrame.rowconfigure(2, weight=1)

# Upper-left entry of grid will be a frame containing the A4 frequency box and its label.
A4Frame = ttk.Frame(A4KeyStatusFrame)
A4Frame.grid(column=0, row=0, sticky="nwes")
A4Label = ttk.Label(A4Frame, text="A4 Frequency in Hz:")
A4Label.grid(column=0, row=0, sticky="nes", padx=1)
A4FreqStr = tk.StringVar(value="440")
A4FreqStrLastConv = tk.StringVar(value="")  # Also track the A4 frequency from the most recent conversion to facilitate detecting when the user updates the A4 frequency text box.
A4Box = ttk.Entry(A4Frame, textvariable=A4FreqStr, width=6)
A4Box.bind("<FocusOut>", A4BoxFocusOut)
A4Box.grid(column=1, row=0, sticky="nws", padx=1)
A4Frame.columnconfigure(0, weight=1)
A4Frame.columnconfigure(1, weight=1)
A4Frame.rowconfigure(0, weight=1)

# Middle-left entry of grid will be the A4 frequency auto-estimation button.
A4AutoEstBtn = ttk.Button(A4KeyStatusFrame, text="Auto-Estimate A4 Frequency", command=A4AutoEstBtnClick)
A4AutoEstBtn.grid(column=0, row=1, sticky="n", padx=5, pady=5)

# Upper-right entry of grid will be the guessed key signature.
keyGuessFrame = ttk.Frame(A4KeyStatusFrame)
keyGuessFrame.grid(column=1, row=0, sticky="nwes")
keyGuessLabel = ttk.Label(keyGuessFrame, text="Guessed Key Signature:")
keyGuessLabel.grid(column=0, row=0, sticky="nes", padx=1)
keyGuess = tk.StringVar(value="TBD")
keyGuessBox = ttk.Entry(keyGuessFrame, textvariable=keyGuess, width=6)
keyGuessBox.state(["disabled"])
keyGuessBox.grid(column=1, row=0, sticky="nws", padx=1)
keyGuessFrame.columnconfigure(0, weight=1)
keyGuessFrame.columnconfigure(1, weight=1)
keyGuessFrame.rowconfigure(0, weight=1)

# Middle-right entry of grid will be the key signature guess button.
keyGuessBtn = ttk.Button(A4KeyStatusFrame, text="Guess Key Signature", command=keyGuessBtnClick)
keyGuessBtn.grid(column=1, row=1, sticky="n", padx=5, pady=5)

# Lower row of grid will be the status message line.
statusMsg = tk.StringVar(value="Status: Ready")
statusLabel = ttk.Label(A4KeyStatusFrame, textvariable=statusMsg, wraplength=1000, justify="center")
statusLabel.grid(column=0, row=2, columnspan=2, sticky="ns", padx=padx_master, pady=(10,5))


# Create third section (sub-frame) with conversion controls and detailed settings.
# This sub-frame will be a 4x2 grid.

convCtrlFrame = ttk.Frame(outermostFrame, relief="ridge")
convCtrlFrame.grid(column=0, row=2, sticky="nwes", padx=padx_master, pady=(5,padx_master))
convCtrlFrame.columnconfigure(0, weight=1)
convCtrlFrame.columnconfigure(1, weight=1)
convCtrlFrame.rowconfigure(0, weight=0, minsize=15)
convCtrlFrame.rowconfigure(1, weight=1)
convCtrlFrame.rowconfigure(2, weight=0, minsize=20)

# First row will be the title label of this section.
convCtrlHeader = ttk.Label(convCtrlFrame, text="Conversion Controls")
convCtrlHeader.grid(column=0, row=0, columnspan=2, sticky="ns", pady=(5,0))

# Second row left column will be the 2 radio buttons controlling the conversion direction.
# Will place these radio buttons inside their own 2x1 frame with a border.
convDirRBsFrame = ttk.Frame(convCtrlFrame, relief="ridge")
convDirRBsFrame.grid(column=0, row=1, sticky="nse", padx=padx_master, pady=5)
convDirRBsFrame.columnconfigure(0, weight=1)
convDirRBsFrame.rowconfigure(0, weight=1)
convDirRBsFrame.rowconfigure(1, weight=1)
convDirIsF2NN = tk.BooleanVar(value=True)
convDirIsF2NN.trace_add("write", warnChangesSinceLastConv)
convDirRB_F2NN = ttk.Radiobutton(convDirRBsFrame, text="Frequencies to note names", variable=convDirIsF2NN, value=True)
convDirRB_F2NN.grid(column=0, row=0, sticky="nse", padx=5, pady=5)
convDirRB_NN2F = ttk.Radiobutton(convDirRBsFrame, text="Note names to frequencies", variable=convDirIsF2NN, value=False)
convDirRB_NN2F.grid(column=0, row=1, sticky="nse", padx=5, pady=(0,5))

# Second row right column will be the 2 radio buttons controlling whether to replace or insert converted items in the output text.
# Will place these radio buttons inside their own 2x1 frame with a border.
replaceModeRBsFrame = ttk.Frame(convCtrlFrame, relief="ridge")
replaceModeRBsFrame.grid(column=1, row=1, sticky="nsw", padx=padx_master, pady=5)
replaceModeRBsFrame.columnconfigure(0, weight=1)
replaceModeRBsFrame.rowconfigure(0, weight=1)
replaceModeRBsFrame.rowconfigure(1, weight=1)
replaceConvItems = tk.BooleanVar(value=True)
replaceConvItems.trace_add("write", warnChangesSinceLastConv)
replaceModeRB_True = ttk.Radiobutton(replaceModeRBsFrame, text="Replace converted items", variable=replaceConvItems, value=True)
replaceModeRB_True.grid(column=0, row=0, sticky="nsw", padx=5, pady=5)
replaceModeRB_False = ttk.Radiobutton(replaceModeRBsFrame, text="Insert converted items under line", variable=replaceConvItems, value=False)
replaceModeRB_False.grid(column=0, row=1, sticky="nsw", padx=5, pady=(0,5))

# Fourth row will have the convert and show detailed settings buttons.
convBtn = ttk.Button(convCtrlFrame, text="Convert", command=convBtnClick, default="active")
convBtn.grid(column=0, row=3, sticky="e", padx=5, pady=(5,10))
showDetSetsBtnText = tk.StringVar(value="Show Detailed Settings")
showDetSetsBtn = ttk.Button(convCtrlFrame, textvariable=showDetSetsBtnText, command=showDetSetsBtnClick)
showDetSetsBtn.grid(column=1, row=3, sticky="w", padx=5, pady=(5,10))
firstConvDone = tk.BooleanVar(value=False)  # Track whether at least one conversion has been done.

# Third (initially hidden) row will have the detailed settings sub-frame, which will be a large 7x2 grid.
detSetsFrame = ttk.Frame(convCtrlFrame, relief="ridge")
detSetsFrame.grid(column=0, row=2, columnspan=2, pady=(5,5))
detSetsFrame_nRows = 8
detSetsFrame_nCols = 2
for k in range(detSetsFrame_nRows):
    detSetsFrame.rowconfigure(k, weight=1)
for k in range(detSetsFrame_nCols):
    detSetsFrame.columnconfigure(k, weight=1)

# Detailed settings header.
detSetsHeader = ttk.Label(detSetsFrame, text="Detailed Settings")
detSetsHeader.grid(column=0, row=0, columnspan=detSetsFrame_nCols, sticky="s", pady=(5,0))

# Cents deviation checkbox.
centsDevCBOn = tk.BooleanVar(value=False)
centsDevCBOn.trace_add("write", warnChangesSinceLastConv)
centsDevCB = ttk.Checkbutton(detSetsFrame, text="Display +/- cents deviations?", variable=centsDevCBOn, onvalue=True, offvalue=False)
centsDevCB.grid(column=0, row=1, columnspan=round(detSetsFrame_nCols/2), sticky="nwes", pady=(5,0), padx=padx_master)

# Sub-sub-frame for overall prefererence of flats, sharps, or automatic selection, which will be a 1x4 grid.
overallEnharmPrefFrame = ttk.Frame(detSetsFrame)
overallEnharmPrefFrame.grid(column=round(detSetsFrame_nCols/2), row=1, columnspan=detSetsFrame_nCols-round(detSetsFrame_nCols/2), sticky="nwes", pady=(5,0), padx=padx_master)  # Position in parent grid cell.
overallEnharmPrefFrame.rowconfigure(0, weight=1)
for k in range(4):
    overallEnharmPrefFrame.columnconfigure(k, weight=1)
overallEnharmPrefLabel = ttk.Label(overallEnharmPrefFrame, text="Use:")
overallEnharmPrefLabel.grid(column=0, row=0, sticky="nes")
overallEnharmPref = tk.StringVar(value="Auto")
overallEnharmPref.trace_add("write", warnChangesSinceLastConv)
prefFlatsRB = ttk.Radiobutton(overallEnharmPrefFrame, text="Flats", variable=overallEnharmPref, value="Flats")
prefFlatsRB.grid(column=1, row=0, sticky="ns")
prefSharpsRB = ttk.Radiobutton(overallEnharmPrefFrame, text="Sharps", variable=overallEnharmPref, value="Sharps")
prefSharpsRB.grid(column=2, row=0, sticky="ns")
prefAutoEnharmRB = ttk.Radiobutton(overallEnharmPrefFrame, text="Auto", variable=overallEnharmPref, value="Auto")
prefAutoEnharmRB.grid(column=3, row=0, sticky="ns")

# Row for preferences regarding enharmonics that correspond to natural notes. These preferences will go into a sub-sub-frame with a 1x8 grid.
natEnharmPrefsFrame = ttk.Frame(detSetsFrame)
natEnharmPrefsFrame.grid(column=0, row=2, columnspan=detSetsFrame_nCols, sticky="ns", pady=(5,0), padx=padx_master)
natEnharmPrefsFrame.rowconfigure(0, weight=1)
numNatEnharmPrefs = 4
for k in range(numNatEnharmPrefs):
    natEnharmPrefsFrame.columnconfigure(k, weight=1)
natEnharmPrefsBoxWidth = 5

useBsharpLabel = ttk.Label(natEnharmPrefsFrame, text="Use B#?")
useBsharpLabel.grid(column=0, row=0, sticky="e")
useBsharpMenuVal = tk.StringVar(value="Auto")
useBsharpMenuVal.trace_add("write", warnChangesSinceLastConv)
useBsharpMenu = ttk.Combobox(natEnharmPrefsFrame, textvariable=useBsharpMenuVal, values=["Auto","Yes","No"], width=natEnharmPrefsBoxWidth)
useBsharpMenu["state"] = "readonly"
useBsharpMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
useBsharpMenu.grid(column=1, row=0, sticky="w")

useCbLabel = ttk.Label(natEnharmPrefsFrame, text="Use Cb?")
useCbLabel.grid(column=2, row=0, sticky="e")
useCbMenuVal = tk.StringVar(value="Auto")
useCbMenuVal.trace_add("write", warnChangesSinceLastConv)
useCbMenu = ttk.Combobox(natEnharmPrefsFrame, textvariable=useCbMenuVal, values=["Auto","Yes","No"], width=natEnharmPrefsBoxWidth)
useCbMenu["state"] = "readonly"
useCbMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
useCbMenu.grid(column=3, row=0, sticky="w")

useEsharpLabel = ttk.Label(natEnharmPrefsFrame, text="Use E#?")
useEsharpLabel.grid(column=4, row=0, sticky="e")
useEsharpMenuVal = tk.StringVar(value="Auto")
useEsharpMenuVal.trace_add("write", warnChangesSinceLastConv)
useEsharpMenu = ttk.Combobox(natEnharmPrefsFrame, textvariable=useEsharpMenuVal, values=["Auto","Yes","No"], width=natEnharmPrefsBoxWidth)
useEsharpMenu["state"] = "readonly"
useEsharpMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
useEsharpMenu.grid(column=5, row=0, sticky="w")

useFbLabel = ttk.Label(natEnharmPrefsFrame, text="Use Fb?")
useFbLabel.grid(column=6, row=0, sticky="e")
useFbMenuVal = tk.StringVar(value="Auto")
useFbMenuVal.trace_add("write", warnChangesSinceLastConv)
useFbMenu = ttk.Combobox(natEnharmPrefsFrame, textvariable=useFbMenuVal, values=["Auto","Yes","No"], width=natEnharmPrefsBoxWidth)
useFbMenu["state"] = "readonly"
useFbMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
useFbMenu.grid(column=7, row=0, sticky="w")

# Row for flat and sharp character style selection buttons.
charStyleFrame = ttk.Frame(detSetsFrame)
charStyleFrame.grid(column=0, row=3, columnspan=detSetsFrame_nCols, sticky="ns", pady=(5,0), padx=padx_master)
charStyleFrame.rowconfigure(0, weight=1)
charStyleFrame.columnconfigure(0, weight=1)
charStyleFrame.columnconfigure(1, weight=1)
charStyleFrame.columnconfigure(2, weight=1)
charStylePrefLabel = ttk.Label(charStyleFrame, text="Flat/Sharp Display Style:")
charStylePrefLabel.grid(column=0, row=0, sticky="nes")
prefFancyChars = tk.BooleanVar(value=False)
prefFancyChars.trace_add("write", warnChangesSinceLastConv)
charStyleSimpleRB = ttk.Radiobutton(charStyleFrame, text="Simple (b, #)", variable=prefFancyChars, value=False)
charStyleSimpleRB.grid(column=1, row=0, sticky="ns")
charStyleFancyRB = ttk.Radiobutton(charStyleFrame, text="Fancy (♭, ♯)", variable=prefFancyChars, value=True)
charStyleFancyRB.grid(column=2, row=0, sticky="ns")


# Row for instrument selection for transposition.
instSelFrame = ttk.Frame(detSetsFrame)
instSelFrame.grid(column=0, row=4, columnspan=detSetsFrame_nCols, sticky="ns", pady=(5,0), padx=padx_master)
instSelFrame.rowconfigure(0, weight=1)
instSelFrame.columnconfigure(0, weight=1)
instSelFrame.columnconfigure(1, weight=1)
instSelLabel = ttk.Label(instSelFrame, text="Instrument (for transposition):")
instSelLabel.grid(column=0, row=0, sticky="e")
instSel = tk.StringVar(value=instsForTransp[0])
instSel.trace_add("write", instSelPossibleChange)
instLengthsMax = max([len(inst) for inst in instsForTransp])
instSelMenu = ttk.Combobox(instSelFrame, textvariable=instSel, values=instsForTransp, width=instLengthsMax+1)
instSelMenu["state"] = "readonly"
instSelMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
instSelMenu.grid(column=1, row=0, sticky="w")

# Row for instrument key and transposition settings.
transpSettingsFrame = ttk.Frame(detSetsFrame)
transpSettingsFrame.grid(column=0, row=5, columnspan=detSetsFrame_nCols, sticky="ns", pady=(5,0), padx=padx_master)
transpSettingsFrame.rowconfigure(0, weight=1)
for k in range(6):
    transpSettingsFrame.columnconfigure(k, weight=1)
instKeyLabel = ttk.Label(transpSettingsFrame, text="Inst Key:")
instKeyLabel.grid(column=0, row=0, sticky="e", padx=(1,0))
instKey = tk.StringVar(value="C")
instKey.trace_add("write", instTranspCustomSettingsChange)
instKeyOpts = "Ab A Bb B C Db D Eb E F Gb G".split()
instKeyMenu = ttk.Combobox(transpSettingsFrame, textvariable=instKey, values=instKeyOpts, width=4)
instKeyMenu.grid(column=1, row=0, sticky="w", padx=(0,1))
instKeyMenu["state"] = "readonly"
instKeyMenu.state(["disabled"])
instKeyMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
transpDirLabel = ttk.Label(transpSettingsFrame, text="Inst Shift Direction:")
transpDirLabel.grid(column=2, row=0, sticky="e", padx=(1,0))
transpDirStr = tk.StringVar(value="Down")
transpDirStr.trace_add("write", instTranspCustomSettingsChange)
transpDirMenu = ttk.Combobox(transpSettingsFrame, textvariable=transpDirStr, values=["Up","Down"], width=6)
transpDirMenu.grid(column=3, row=0, sticky="w", padx=(0,1))
transpDirMenu["state"] = "readonly"
transpDirMenu.state(["disabled"])
transpDirMenu.bind("<<ComboboxSelected>>", deselReadOnlyCBText)
instOctLabel = ttk.Label(transpSettingsFrame, text="Inst Extra Octave Shift:")
instOctLabel.grid(column=4, row=0, sticky="e", padx=(1,0))
instOctShiftStr = tk.StringVar(value="0")
instOctShiftStr.trace_add("write", instTranspCustomSettingsChange)
instOctBox = ttk.Entry(transpSettingsFrame, textvariable=instOctShiftStr, width=3)
instOctBox.grid(column=5, row=0, sticky="w", padx=(0,1))
instOctBox.state(["disabled"])

# Row for displaying final instrument transposition shift.
transpFinalShiftStr = tk.StringVar(value="0")
transpFinalShiftStr.trace_add("write", transpFinalShiftStrChange)
transpFinalShiftLabelStr = tk.StringVar(value="Half-steps inst sounds above written pitch: {0:d}".format(read_transpFinalShiftStr()))
transpFinalShiftLabel = ttk.Label(detSetsFrame, textvariable=transpFinalShiftLabelStr)
transpFinalShiftLabel.grid(column=0, row=6, columnspan=2, sticky="ns", pady=(5,0), padx=padx_master)
#transpFinalShiftLabel.grid_remove()  # Hide this row of widgets to simplify the interface.

# Last row in detailed preferences frame grid is the button for restoring default values for detailed settings.
restoreDefaultDetSetsBtn = ttk.Button(detSetsFrame, text="Restore Defaults", command=restoreDefaultDetSetsBtnClick)
restoreDefaultDetSetsBtn.grid(column=0, row=7, columnspan=detSetsFrame_nCols, sticky="n", pady=(5,10))

# Start with detailed settings hidden.
detSetsFrame.grid_remove()

# Get screen dimensions, and then resize and reposition the window to fit.
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
win_width = round(0.7*screen_width)
win_height = round(0.7*screen_height)
win_hshift = round(screen_width/10)
win_vshift = round(screen_height/10)
win_init_geometry = "{0:d}x{1:d}+{2:d}+{3:d}".format(win_width, win_height, win_hshift, win_vshift)
root.geometry(win_init_geometry)

# Start app.
root.mainloop()
