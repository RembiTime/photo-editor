# A program for users to edit colors in images based on grayscale values
# Rhyder Swen
# 10/19/21

import cv2
import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter import colorchooser
from tkmacosx import Button
import PIL.Image, PIL.ImageTk
import numpy 
import random
import webbrowser
from functools import partial
import os
import subprocess
import threading
import json

# Randomly generates 3 RGB colors, and then converts them to hex (hex is just base-16 RGB)
colorsRGB = [(random.randint(0,255), random.randint(0,255), random.randint(0,255)), (random.randint(0,255), random.randint(0,255), random.randint(0,255))]
colorsHex = ["#%02x%02x%02x" % colorsRGB[0], "#%02x%02x%02x" % colorsRGB[1]]
grayscaleBreaks = [0, 127.5, 255]
activeColor = 0
deletingColor = False

# Method for creating rectangles with smooth corners because it looks nicer
def round_rectangle(x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]

    return grayscaleGraphic.create_polygon(points, **kwargs, smooth=True)

# Create a window
window = tk.Tk()
window.title("Pick your darn file")

# Opens the file selector for the user to chose which file to open, then saves the path in baseFilename
filename = askopenfilename(title = "Select an image", filetypes = (("JPEG", ".jpeg"), ("JPG", ".jpg"), ("PNG", ".png")))
baseFilename = os.path.basename(filename)

window.title(baseFilename)

# Load an image using OpenCV
original_image = cv2.imread(filename)
grayscale_image_simple = cv2.imread(filename, 0)
grayscale_image = cv2.cvtColor(grayscale_image_simple, cv2.COLOR_GRAY2BGR)

# Save the image's dimensions
image_height = original_image.shape[0]
image_width = original_image.shape[1]
image_channels = original_image.shape[2]

# Resize Images to fit the screensize
screenHeight = window.winfo_screenheight()
screenWidth = window.winfo_screenwidth()

percentChange = 1
width = image_width
height = image_height
# Checks if the image dimensions are too big (more than half the screen width or 1/3.5 the screen height)
if image_height > screenHeight/3.5 or image_width > screenWidth / 2:
    # If the height is the issue (The width will be smaller than that largest it needs to be when proportionally shrinked)
    if image_height / image_width > (screenHeight/3.5)/(screenWidth/2):
        percentChange = (screenHeight/3.5) / image_height
        height = screenHeight/3.5
        width = image_width * percentChange
    else: 
        # Probably won't be used, but just in case!
        percentChange = (screenWidth / 2) / image_width
        width = screenWidth / 2
        height = image_height * percentChange

# Convert from BGR to RGB because RGB is better in every way and also tkinter uses it
cv_og_img = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
cv_gray_img = cv2.cvtColor(grayscale_image, cv2.COLOR_BGR2RGB)

# Shrinks the images so that they fit on the screen
cv_og_img = cv2.resize(cv_og_img, (0,0), fx=percentChange, fy=percentChange)
cv_gray_img = cv2.resize(cv_gray_img, (0,0), fx=percentChange, fy=percentChange)

# Runs when you click on the grayscale slider graphic. Either updates the current color or deletes the clicked color
def grayscale_clicked(event):
    global activeColor
    global deletingColor
    # Find which rectangle (and by extension, the color number) that was clicked
    rectangleID = event.widget.find_closest(event.x, event.y)[0]
    colorClicked = grayscaleGraphic.find_all().index(rectangleID)
    if not deletingColor:
        activeColor = colorClicked
        selectedColor.set("Selected Color: " + str(activeColor+1))
        # Sets the current value to be what we need it to be because there's no easy way to do it
        s2.config(to=300)
        s2.config(from_=activeColor+1)
        s2.config(from_=-1)
        s2.config(to=activeColor+1)
        s2.config(to=spinNum1.get())
        s2.config(from_=1)
        value_changed()
    else:
        # Delete the color clicked
        colorsHex.pop(colorClicked)
        colorsRGB.pop(colorClicked)
        grayscaleBreaks.pop(colorClicked)
        activeColor -= 1
        # Sets the current value to be what we need it to be because there's no easy way to do it
        s1.config(from_=-300)
        s1.config(to=len(colorsHex))
        s1.config(to=16)
        s1.config(from_=2)

        s2.config(from_=-300)
        s2.config(to=activeColor+1)
        s2.config(to=len(colorsHex))
        s2.config(from_=1)
        # Reset the grayscale breaks to be even
        for x in range(len(colorsHex)):
            grayscaleBreaks[x] = (255/len(colorsHex)) * x
        deletingColor = False
        grayscaleLabel.set("Grayscale Values:")
        l3.config(fg = "white")
        spinbox1_changed()

# Runs on mouse motion
def grayscale_cursor(e):
    #checks whether the mouse is inside the boundaries, if it is, set the cursor to our lord and savior gumby, otherwise, set it back to the default mouse
    if 4 <= e.x and 516 >= e.x and 9 <= e.y and 16 >= e.y:
        grayscaleGraphic.config(cursor="gumby")
    else:
        grayscaleGraphic.config(cursor="")

# Runs whenever absolutely anything is changed. Updates the images on the canvas, button colors, grayscale graphic, etc
def value_changed():
    global image_parts
    global customized_image
    image_parts = []
    customized_image = numpy.zeros((image_height,image_width,image_channels), numpy.uint8)
    # Creates each part of the image: Creates an image of a pure color, gets the parts of the image to replace based on the grayscale values, creates a mask of that color, and then combines that part with the others
    for x in range(len(colorsRGB)):
        paper = numpy.zeros((image_height,image_width,image_channels), numpy.uint8)
        paper[0:image_height,0:image_width, 0:image_channels] = [colorsRGB[x][2],colorsRGB[x][1],colorsRGB[x][0]]
        min_grayscale = [grayscaleBreaks[x],grayscaleBreaks[x],grayscaleBreaks[x]]
        max_grayscale = [grayscaleBreaks[x+1],grayscaleBreaks[x+1],grayscaleBreaks[x+1]]
        min_grayscale = numpy.array(min_grayscale, dtype = "uint8")
        max_grayscale = numpy.array(max_grayscale, dtype = "uint8")
        block_all_but_color = cv2.inRange(grayscale_image, min_grayscale, max_grayscale)
        parts_of_image = cv2.bitwise_or(paper, paper, mask = block_all_but_color)
        image_parts.append(parts_of_image)
        customized_image = cv2.bitwise_or(customized_image, parts_of_image)

    # Converts image to RGB because tkinter
    cv_single_color_img = cv2.cvtColor(image_parts[activeColor], cv2.COLOR_BGR2RGB)
    cv_custom_img = cv2.cvtColor(customized_image, cv2.COLOR_BGR2RGB)

    # Resizes the images to fit on the screen
    cv_single_color_img_small = cv2.resize(cv_single_color_img, (0,0), fx=percentChange, fy=percentChange)
    cv_custom_img_small = cv2.resize(cv_custom_img, (0,0), fx=percentChange, fy=percentChange)

    global photo3
    global photo4
    # Converts the images from opencv to pillow/tkinter
    photo3 = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_single_color_img_small))
    photo4 = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_custom_img_small))

    # Updates the images on the window
    canvas.itemconfig(pic3, image = photo3)
    canvas.itemconfig(pic4, image = photo4)

    # Update the buttons to match the selected color
    b1.configure(bg=colorsHex[activeColor])
    b2.configure(bg=colorsHex[activeColor])
    b3.configure(bg=colorsHex[activeColor])
    b4.configure(bg=colorsHex[activeColor])

    # Determines if text on the buttons should be black or white for readability
    if (colorsRGB[activeColor][0]*0.299 + colorsRGB[activeColor][1]*0.587 + colorsRGB[activeColor][2]*0.114) > 186:
        b1.configure(fg="black")
        b2.configure(fg="black")
        b3.configure(fg="black")
        b4.configure(fg="black")
    else:
        b1.configure(fg="white")
        b2.configure(fg="white")
        b3.configure(fg="white")
        b4.configure(fg="white")

    # Updates the label which says the color value of the selected color
    currentColorValues.set("Hex: " + colorsHex[activeColor] + "  -  RGB: " + str(colorsRGB[activeColor][0]) + ", " + str(colorsRGB[activeColor][1]) + ", " + str(colorsRGB[activeColor][2]))

    # Disables the delete buttons if the value is 2, enables if it is more than 2
    if spinNum1.get() == "2":
        b3.configure(state=tk.DISABLED,cursor="")
        b4.configure(state=tk.DISABLED,cursor="")
    else:
        b3.configure(state=tk.NORMAL,cursor="gumby")
        b4.configure(state=tk.NORMAL,cursor="gumby")

    # If the selected color is not the last color, set the grayscale slider equal to the current value for the color and update the limits before overlapping with the next color
    if activeColor+1 != len(colorsHex):
        tb1.config(from_=grayscaleBreaks[activeColor]+1, to=grayscaleBreaks[activeColor+2]-1, fg="white")
        tb1.set(grayscaleBreaks[activeColor+1])
    # If it is the last color, set the value to 0 and make the number gray so you can't slide it because the last color should always be 255
    else:
        tb1.config(from_=-1, to=1, fg="gray")
        tb1.set(0)

    # Reset the grayscale slider graphic
    grayscaleGraphic.delete("all")
    grayscaleRectangles = []
    grayscaleHandles = []
    
    # Creates a round rectangle for each color based on its amount of grayscale along with its handle
    for x in range(len(colorsHex)):
        grayscaleRectangles.append(round_rectangle(grayscaleBreaks[x]*2+10, 10, grayscaleBreaks[x+1]*2+10, 15, radius=5, fill=colorsHex[x]))
        grayscaleGraphic.tag_bind(grayscaleRectangles[x], "<Button-1>", grayscale_clicked)
    # Seperate so it overlaps the other
    for x in range(len(colorsHex)-1):
        grayscaleHandles.append(round_rectangle(grayscaleBreaks[x+1]*2+7, 5, grayscaleBreaks[x+1]*2+13, 20, radius=5, fill=colorsHex[x]))

# Creates the image canvas
canvas = tk.Canvas(window, width = width * 2, height = height * 2)
canvas.grid(column=0,row=0,columnspan=10, padx=10)

# Use PIL (Pillow) to convert the NumPy ndarray from cv2 to a PhotoImage
photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_og_img))
photo2 = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_gray_img))
photo3 = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_og_img))
photo4 = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(cv_og_img))


# Add the photos to the Canvas
pic = canvas.create_image(0, 0, image=photo, anchor=tk.NW)
pic2 = canvas.create_image(width, 0, image=photo2, anchor=tk.NW)
pic3 = canvas.create_image(0, height, image=photo3, anchor=tk.NW)
pic4 = canvas.create_image(width, height, image=photo4, anchor=tk.NW)

# Create the canvas for the grayscale graphic
grayscaleGraphic = tk.Canvas(window, height=50,width=530)
grayscaleGraphic.grid(row=3,column=1,rowspan=2,columnspan=7,sticky=tk.NW)
grayscaleGraphic.bind("<Motion>",grayscale_cursor)
grayscaleRectangles = []
grayscaleHandles = []

# Runs when the "Change color" button is pressed
def change_color():
    # Open the built-in color picker
    pickedColor = colorchooser.askcolor(colorsHex[activeColor], title="Choose a color!")
    # If the dialogue is not cancelled, update the active colors
    if pickedColor[0] != None:
        colorsRGB[activeColor] = pickedColor[0]
        colorsHex[activeColor] = pickedColor[1]
        value_changed()

# Runs when the "Delete this color" button is pressed
def delete_this_color():
    # This if statement doesn't really *need* to be here since the button should be disabled, but just in case
    if len(colorsHex) > 2:
        global activeColor
        # Deletes the current color and update the selected color
        colorsHex.pop(activeColor)
        colorsRGB.pop(activeColor)
        grayscaleBreaks.pop(activeColor)
        if activeColor >= len(colorsHex):
            activeColor -= 1
        # Sets the current value to be what we need it to be because there's no actual way
        s1.config(from_=-300)
        s1.config(to=len(colorsHex))
        s1.config(to=16)
        s1.config(from_=2)

        s2.config(from_=-300)
        s2.config(to=activeColor+1)
        s2.config(to=len(colorsHex))
        s2.config(from_=1)

        # Reset the grayscale breaks to be even
        for x in range(len(colorsHex)):
            grayscaleBreaks[x] = (255/len(colorsHex)) * x
        spinbox1_changed()

# Runs when the "Delete a color" button is pressed
def delete_a_color():
    # Again, the if statement doesn't really need to be here, but just in case
    if len(colorsHex) > 2:
        global deletingColor
        # If you aren't already deleting a color, set the grayscale label to be red instructing the user to click a color to delete
        if not deletingColor:
            grayscaleLabel.set("Click a color to delete!")
            l3.config(fg = "#ff7575")
            deletingColor = True
        # If you already are deleting a color, revert the grayscale label
        else:
            grayscaleLabel.set("Grayscale Values:")
            l3.config(fg = "white")
            deletingColor = False

# Runs when the "Color palettes" button is pressed and controls everything in the color palette menu while it is open
paletteMenu = None
def open_color_palette_menu():
    global paletteMenu
    # If a paletteMenu already exists, close it
    if paletteMenu is not None and paletteMenu.winfo_exists():
        paletteMenu.destroy()
    
    # Saves what's stored in palettes.json into the variable 'data'
    with open("palettes.json", "r") as read_file:
        data = json.load(read_file)

    # Creates the palette menu
    paletteMenu = tk.Toplevel()
    paletteMenu.title("Color Palette Menu")

    defaultPalettes = []
    createdPalettes = []

    # Creates a list of all the color palette names
    for paletteName in data["Defaults"].keys():
        defaultPalettes.append(paletteName)
    for paletteName in data["Created"].keys():
        createdPalettes.append(paletteName)
    
    palettes = ["Built-in Palettes:"]
    palettes.extend(defaultPalettes)
    if len(createdPalettes) > 0:
        palettes.append("Created Palettes:")
        palettes.extend(createdPalettes)

    # Creates a canvas for the preview colors to go
    previewCanvas = tk.Canvas(paletteMenu, width = 150, height = 50)
    previewCanvas.grid(row=1,column=1,rowspan=4,padx=(0,10),sticky=tk.N)
    
    previewSquares = []
    previewPercents = []
    previewPercentsOutlines = []
    colorRow = 0

    # Runs if your mouse enters a preview color square and replaces the percent to the hex value of the color
    def entered_square(event=""):
        palette = option.get()
        if option.get() == "Select Palette":
            palette = "Pastel"
        
        # Gets if the palette is a created or a default palette
        paletteSection = "Created"
        if palette in defaultPalettes:
            paletteSection = "Defaults"

        #Finds the id of the square
        squareID = event.widget.find_closest(event.x, event.y)[0]

        # Finds the color index from the palette (Divided by 6 because we create 5 text objects to every one square)
        colorClicked = int((previewCanvas.find_all().index(squareID)) / 6)

        # Updates all the text with the tag percent<ColorNum> to show the hex value instead at a smaller font size
        tagName = "percent" + str(colorClicked)
        smallFont = tkFont.nametofont("TkDefaultFont").copy()
        smallFont.configure(size=9)
        previewCanvas.itemconfig(tagName, text=data[paletteSection][palette]["Colors"][colorClicked], font=smallFont)
    
    # Runs if your mouse leaves a preview color square and replaces the hex value to the percent of the color
    def left_square(event=""):
        palette = option.get()
        if option.get() == "Select Palette":
            palette = "Pastel"
        
        paletteSection = "Created"
        if palette in defaultPalettes:
            paletteSection = "Defaults"

        # Sometimes the mouse position it records is closer to another square, so just update all squares to go back to the percent values
        for x in range(len(data[paletteSection][palette]["Colors"])):
            tagName = "percent" + str(x)
            percentGrayscale = str(round(((data[paletteSection][palette]["Grayscale Breaks"][x+1] - data[paletteSection][palette]["Grayscale Breaks"][x]) / 255) * 100, 1)) + "%"
            previewCanvas.itemconfig(tagName, text=percentGrayscale, font="TkDefaultFont")
        
    # Creates the initial preview squares/percents
    for x in range(len(data["Defaults"]["Pastel"]["Colors"])):
        # If this is the fourth/seventh/etc color, make it go on the next line
        if x % 3 == 0 and x != 0:
            colorRow += 1
            previewCanvas.config(height=(colorRow+1)*50)
        
        # Update the x position. 1 = 0, 2 = 50, 3 = 100, 4 = 0, etc.
        xPos = x * 50
        while xPos > 100:
            xPos -= 150

        # Creates the squares and adds them to a list
        squareTag = "squaria" + str(x)
        previewSquares.append(previewCanvas.create_rectangle(xPos, colorRow*50, xPos+48, colorRow*50+48, fill=data["Defaults"]["Pastel"]["Colors"][x], outline="", tags=squareTag))

        # Gets the percent of the image the color will take up based on its grayscale values
        percentGrayscale = str(round(((data["Defaults"]["Pastel"]["Grayscale Breaks"][x+1] - data["Defaults"]["Pastel"]["Grayscale Breaks"][x]) / 255) * 100, 1)) + "%"
        
        # Creates the percent text (There is no built-in outline for text, so I had to improvise)
        textTag = "percent" + str(x)
        previewPercentsOutlines.append(previewCanvas.create_text((xPos+24, colorRow*50+39), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
        previewPercentsOutlines.append(previewCanvas.create_text((xPos+24, colorRow*50+41), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
        previewPercentsOutlines.append(previewCanvas.create_text((xPos+26, colorRow*50+39), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
        previewPercentsOutlines.append(previewCanvas.create_text((xPos+26, colorRow*50+41), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
        previewPercents.append(previewCanvas.create_text((xPos+25, colorRow*50+40), text=percentGrayscale, state=tk.DISABLED, tags=[textTag, squareTag]))

        previewCanvas.tag_bind(squareTag, "<Enter>", entered_square)
        previewCanvas.tag_bind(squareTag, "<Leave>", left_square)

    # The value of the OptionMenu
    option = tk.StringVar(window)
    option.set("Select Palette")

    # Runs when the OptionMenu's value is changed
    def update_selected(event=""):
        # Reset the preview canvas
        previewCanvas.delete("all")
        previewSquares = []
        previewPercents = []
        previewPercentsOutlines = []
        previewCanvas.config(height=50)

        # Gets if the newly selected palette was a default or a created palette
        paletteSection = "Created"
        b6.config(state=tk.NORMAL)
        if option.get() in defaultPalettes:
            paletteSection = "Defaults"
            b6.config(state=tk.DISABLED)
        
        # Creates the squares and percents the same way as above except with whatever the currently selected palette is instead of just for pastel, so I'm just not gonna comment the same things again
        colorRow = 0
        for x in range(len(data[paletteSection][option.get()]["Colors"])):
            if x % 3 == 0 and x != 0:
                colorRow += 1
                previewCanvas.config(height=(colorRow+1)*50)
        
            xPos = x * 50
            while xPos > 100:
                xPos -= 150

            squareTag = "squaria" + str(x)
            previewSquares.append(previewCanvas.create_rectangle(xPos, colorRow*50, xPos+48, colorRow*50+48, fill=data[paletteSection][option.get()]["Colors"][x], outline="", tags=squareTag))

            percentGrayscale = str(round(((data[paletteSection][option.get()]["Grayscale Breaks"][x+1] - data[paletteSection][option.get()]["Grayscale Breaks"][x]) / 255) * 100, 1)) + "%"

            textTag = "percent" + str(x)
            previewPercentsOutlines.append(previewCanvas.create_text((xPos+24, colorRow*50+39), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
            previewPercentsOutlines.append(previewCanvas.create_text((xPos+24, colorRow*50+41), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
            previewPercentsOutlines.append(previewCanvas.create_text((xPos+26, colorRow*50+39), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
            previewPercentsOutlines.append(previewCanvas.create_text((xPos+26, colorRow*50+41), text=percentGrayscale, fill="black", state=tk.DISABLED, tags=[textTag, squareTag]))
            previewPercents.append(previewCanvas.create_text((xPos+25, colorRow*50+40), text=percentGrayscale, state=tk.DISABLED, tags=[textTag, squareTag]))

            previewCanvas.tag_bind(squareTag, "<Enter>", entered_square)
            previewCanvas.tag_bind(squareTag, "<Leave>", left_square)
            
        # For some reason, the canvas doesn't fully update unless I change the dimensions by at least 1 pixel
        if previewCanvas["width"] == "150":
            previewCanvas.config(width=151)
        else:
            previewCanvas.config(width=150)

    # Create the OptionMenu
    om1 = tk.OptionMenu(paletteMenu, option, *palettes, command=update_selected)
    om1.grid(row=0,column=0,padx=10, pady=10)

    # Disable the labels for Built-in Palettes and Created Palettes because they're just seperators
    om1['menu'].entryconfigure("Built-in Palettes:", state = "disabled")
    if len(createdPalettes) > 0:
        om1['menu'].entryconfigure("Created Palettes:", state = "disabled")
    
    # Runs when the palettes to be shown OptionMenu have changed
    def update_palettes():
        menuValues = om1["menu"]
        values = []
        # Gets the values currently stored in the OptionMenu
        for index in range(menuValues.index("end") + 1):
            values.append(menuValues.entrycget(index, "label"))
        
        # Delete everything past Created Palettes if it doesn't just end at created palettes because that creates duplicates of everything
        if values[-1] != "Created Palettes:" and values[-1] != defaultPalettes[-1] or len(createdPalettes) == 0:
            om1["menu"].delete(len(defaultPalettes)+1, "end")
        # If the length of created palettes is more than 0, add the Created Palettes label, disable it, and add the labels necessary
        if len(createdPalettes) != 0:
            om1["menu"].add_command(label="Created Palettes:")
            om1['menu'].entryconfigure("Created Palettes:", state = "disabled")
            for paletteName in data["Created"].keys():
                om1["menu"].add_command(label=paletteName,command=tk._setit(option, paletteName, update_selected))
    
    # Runs when the "Apply Palette" button is pushed
    def apply_palette():
        if option.get() == "Select Palette":
            option.set("Pastel")
        
        # Finds if it is a default or created palette
        paletteSection = "Created"
        if option.get() in defaultPalettes:
            paletteSection = "Defaults"

        global colorsHex
        global colorsRGB
        global grayscaleBreaks
        # Set the images' hex colors and grayscale breaks equal to the palette's
        colorsHex = data[paletteSection][option.get()]["Colors"]
        grayscaleBreaks = data[paletteSection][option.get()]["Grayscale Breaks"]

        # Convert hex to RGB. RGB is just base-10 while Hex is base-16 and add those values to the images' RGB values
        colorsRGB = []
        for x in range(len(colorsHex)):
            colorsRGB.append((int(colorsHex[x][1:3], 16), int(colorsHex[x][3:5], 16), int(colorsHex[x][5:7], 16)))

        value_changed()
        # Close the palette menu
        paletteMenu.destroy()

    # Runs if the "Delete Palette" button is pressed
    def delete_palette():
        # Only runs if it is a created palette
        if option.get() in createdPalettes:
            # Delete the palette and update the json file
            data["Created"].pop(option.get())
            with open("palettes.json", "w") as write_file:
                json.dump(data, write_file, indent=4)

            # Finds what to change the new palette to
            paletteIndex = createdPalettes.index(option.get())
            # If there are no other created palettes, set it to the top default palette
            if len(createdPalettes) == 1:
                option.set(defaultPalettes[-1])
                b6.config(state=tk.DISABLED)
            # If it is the last palette, go to the one before it
            elif paletteIndex == len(createdPalettes) - 1:
                option.set(createdPalettes[-2])
            # Otherwise, go to the palette above it
            else:
                option.set(createdPalettes[paletteIndex+1])
            createdPalettes.pop(paletteIndex)
            update_palettes()
            update_selected()

    global textWindow
    textWindow = None
    # Runs when the "Save Palette" button is pressed and manages everything in the text window
    def save_palette():
        global textWindow
        # If a text window already exists, delete it
        if textWindow is not None and textWindow.winfo_exists():
            textWindow.destroy()

        # Creates the text window
        textWindow = tk.Toplevel()
        textWindow.title("Pick a name!")

        # Creates the variable the stores what the inputted text is
        paletteInput = tk.StringVar(window, value=0)
        paletteInput.set("2")

        # Checks to make sure the length of the entered text is under 50 so it isn't TOO long
        def test_val(inStr,acttyp):
            if acttyp == '1' and len(inStr) > 50: #if text is inserted and the characters are greater than 50
                return False
            return True

        # Creates the text entry box
        e1 = tk.Entry(textWindow, validate="key")
        e1['validatecommand'] = (e1.register(test_val),'%P','%d')
        e1.pack()

        def close_text_window(event=""):
            global paletteMenu
            # Only run if a paletteMenu exists
            if paletteMenu is not None and paletteMenu.winfo_exists():
                # If the picked name is already taken in a default color palette, don't let it save
                if e1.get() in data["Defaults"].keys() or e1.get() in data["Created"].keys():
                    b9.config(text="Already taken!", fg="red")
                else:
                    # Save the inputted name, destroy the window, and add the values to the palette
                    paletteName = e1.get()
                    textWindow.destroy()
                    data["Created"][paletteName] = {"Colors": [], "Grayscale Breaks": []}

                    for x in range(len(grayscaleBreaks)):
                        if x != 0:
                            # There's one more grayscale break than color
                            data["Created"][paletteName]["Colors"].append(colorsHex[x-1])
                        data["Created"][paletteName]["Grayscale Breaks"].append(grayscaleBreaks[x])

                    # Update the json file and variables
                    with open("palettes.json", "w") as write_file:
                        json.dump(data, write_file, indent=4)
                    createdPalettes.append(paletteName)
                    option.set(paletteName)
                    update_palettes()
                    update_selected()
            else:
                textWindow.destroy()

        # Create the Done button
        b9 = Button(textWindow, text="Done", cursor="gumby", command=close_text_window)
        b9.pack()

        def quit_window(event=""):
            textWindow.destroy()

        # Binds the escape key to closing the window and the return key to submitting
        textWindow.bind("<Escape>", quit_window)
        textWindow.bind("<Return>", close_text_window)
    
    # Runs whenever the "cancel" button is clicked and closes the palette menu (and text window if it's open)
    def close_palette_menu(event=""):
        global textWindow
        paletteMenu.destroy()
        if textWindow is not None and textWindow.winfo_exists():
            textWindow.destroy()
    
    # Create buttons!
    b5 = Button(paletteMenu, text="Apply Palette", cursor="gumby", width=135, height=27, command=apply_palette)
    b5.grid(row=1,column=0,padx=10,pady=(0,10))

    b6 = Button(paletteMenu, text="Delete Palette", cursor="gumby", width=135, height=27, command=delete_palette, state=tk.DISABLED, disabledforeground="black")
    b6.grid(row=2,column=0,padx=10,pady=(0,10))
    
    b7 = Button(paletteMenu, text="Create Palette", cursor="gumby", width=135, height=27, command=save_palette)
    b7.grid(row=3,column=0, padx=10,pady=(0,10))

    b8 = Button(paletteMenu, text="Cancel", cursor="gumby", width=135, height=27, command=close_palette_menu)
    b8.grid(row=4,column=0, padx=10,pady=(0,10))

    l5 = tk.Label(paletteMenu, text="Color Preview:")
    l5.grid(row=0,column=1, padx=(0,10))

    # Binds the escape key to closing the menu
    paletteMenu.bind("<Escape>", close_palette_menu)

# Create buttons!
b1 = Button(window, text="Change Color", command=change_color, bg=colorsHex[0], cursor="gumby", width=135, height=27)
b1.grid(row=4,column=1,sticky=tk.SW)

b2 = Button(window, text="Color Palettes", bg=colorsHex[0], cursor="gumby", width=135, height=27, command=open_color_palette_menu)
b2.grid(row=5,column=1,sticky=tk.NW,pady=10)

b3 = Button(window, text="Delete a Color", bg=colorsHex[0], cursor="gumby", width=135, height=27, command=delete_a_color, disabledforeground="black")
b3.grid(row=4, column=4, sticky=tk.SW, padx=(0,10))

b4 = Button(window, text="Delete this Color", bg=colorsHex[0], cursor="gumby", width=135, height=27, command=delete_this_color, disabledforeground="black")
b4.grid(row=5, column=4, sticky=tk.NW, pady=10, padx=(0,10))

spinNum1 = tk.StringVar(window, value=0)
spinNum1.set(2)

# Runs when the grayscale slider is changed and updates the grayscale breaks
def change_grayscale(value):
    if activeColor+1 != len(colorsHex):
        grayscaleBreaks[activeColor+1] = int(value)
    value_changed()

# Create the grayscale slider
tb1 = tk.Scale(window, from_=grayscaleBreaks[0]+1, to=grayscaleBreaks[2]-1, orient=tk.HORIZONTAL, length=250, command=change_grayscale, cursor="gumby")
tb1.grid(row=5, column=2, columnspan=2, padx=(30,50), pady=(0,10), sticky=tk.NW)
tb1.set(grayscaleBreaks[1])

currentColorValues = tk.StringVar(window)

value_changed()

# Creates the number of colors variable - ok I'm gonna stop putting comments like this because it should be self explanitory at this point
numColors = tk.StringVar(window)
numColors.set("Number of Colors: " + str(2))

l1 = tk.Label(window, textvariable=numColors, width=14, anchor=tk.W)
l1.grid(row=2, column=0, sticky=tk.W, padx=10)

# Runs when spinbox 1 (Number of colors) is changed
def spinbox1_changed():
    # Update spinbox 1 (Selected color) based on the new value
    s2.configure(to=spinNum1.get())
    # Update the labels to match the new values
    numColors.set("Number of Colors: " + str(spinNum1.get()))
    selectedColor.set("Selected Color: " + str(spinNum2.get()))

    global activeColor
    # Update the active color
    activeColor = int(spinNum2.get()) - 1

    # Delete colors and grayscale breaks until they are at the right length as the number of colors
    while len(colorsHex) > int(spinNum1.get()):
        colorsHex.pop()
        colorsRGB.pop()
        grayscaleBreaks.pop(0)

    # Add colors and grayscale breaks until they are at the right length as the number of colors
    while len(colorsHex) < int(spinNum1.get()):
        colorsRGB.append((random.randint(0,255), random.randint(0,255), random.randint(0,255)))
        colorsHex.append("#%02x%02x%02x" % colorsRGB[len(colorsHex)])
        grayscaleBreaks.append(255)
    
    # Update the grayscale breaks to be even
    for x in range(len(colorsHex)):
        grayscaleBreaks[x] = (255/len(colorsHex)) * x
    value_changed()

s1 = tk.Spinbox(window, from_=2, to=16, textvariable=spinNum1, command=spinbox1_changed, wrap=True, width=10, buttoncursor="gumby")
s1.grid(row=3, column=0, sticky=tk.W, padx=10)

selectedColor = tk.StringVar(window)
selectedColor.set("Selected Color: " + str(1))

l2 = tk.Label(window, textvariable=selectedColor)
l2.grid(row=4, column=0, sticky=tk.SW, padx=10, pady=(10,0))

# Runs whenever spinbox 2 (Selected color) is changed and updates the label and active color
def spinbox2_changed():
    selectedColor.set("Selected Color: " + str(spinNum2.get()))
    global activeColor
    activeColor = (int(spinNum2.get()) - 1)
    value_changed()

spinNum2 = tk.StringVar(window, value=0)
s2 = tk.Spinbox(window, from_=1, to=2, textvariable=spinNum2, command=spinbox2_changed, wrap=True, width=10, buttoncursor="gumby")
s2.grid(row=5, column=0, sticky=tk.NW, padx=10, pady=5)

grayscaleLabel = tk.StringVar(window)
grayscaleLabel.set("Grayscale Values:")

l3 = tk.Label(window, textvariable=grayscaleLabel)
l3.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=(10,0))

l4 = tk.Label(window, textvariable=currentColorValues)
l4.grid(row=2, column=2, columnspan=3, sticky=tk.SE, padx=(0,75))

l5 = tk.Label(window, text="Grayscale Editor:")
l5.grid(row=4, column=2, sticky=tk.NW, padx=40, pady=(10,0))

# 👀
def open_unsuspicious_video():
    webbrowser.open("https://www.youtube.com/watch?v=dQw4w9WgXcQ",new=1)

# Runs whenever an image is called to save
def save_file(image, event=""):
    # Open built-in function to select the location for the file and saves the specified image
    filepath = asksaveasfilename(defaultextension=".jpg", filetypes = (("JPEG", ".jpeg"), ("JPG", ".jpg"), ("PNG", ".png")))
    if image == "customized":
        cv2.imwrite(filepath,customized_image)
    elif image == "grayscale":
        cv2.imwrite(filepath,cv_gray_img)
    elif image == "single":
        cv2.imwrite(filepath,image_parts[activeColor])

# Gee, I wonder what this does
def quit(event=""):
    window.destroy()

# Runs whenever the "Open" button is pushed and basically just runs the program again
def new_tab():
    def open_new_tab():
        subprocess.call(["python3", os.path.abspath(__file__)])
    newWindow = threading.Thread(target=open_new_tab)
    newWindow.start()

# Bind the s key to save and the escape key to quit
window.bind("s", partial(save_file, "customized"))
window.bind("<Escape>", quit)

# Create the menu options in the top left of the screen
menu = tk.Menu(window)
fileMenu = tk.Menu(menu)
fileMenu.add_command(label="Open", command=new_tab)

saveMenu = tk.Menu(fileMenu)
saveMenu.add_command(label="Save Customized Image", command=partial(save_file, "customized"))
saveMenu.add_command(label="Save Grayscale Image", command=partial(save_file, "grayscale"))
saveMenu.add_command(label="Save Selected Part of Image", command=partial(save_file, "single"))

unsuspiciousMenu = tk.Menu(fileMenu)
unsuspiciousMenu.add_command(label="This is the wrong thing to click", command=open_unsuspicious_video)

fileMenu.add_cascade(label="Save", menu=saveMenu, command=partial(save_file, "customized"))
fileMenu.add_command(label="Quit", command=quit)
menu.add_cascade(label="File", menu=fileMenu)
menu.add_cascade(label="<-- You can click this!", menu=unsuspiciousMenu)
window.config(menu=menu)

# Loop until all windows are closed or you quit
window.mainloop()