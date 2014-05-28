# --------------------------------------------------------------------------- #
# SHAPEDBUTTON Control wxPython IMPLEMENTATION
# Python Code By:
#
# Andrea Gavana, @ 18 Oct 2005
# Latest Revision: 18 Oct 2005, 21.50 CET
#
#
# TODO List/Caveats
#
# 1. Elliptic Buttons May Be Handled Better, In My Opinion. They Look Nice
#    But They Are Somewhat More Difficult To Handle When Using Sizers.
#    This Is Probably Due To Some Lack In My Implementation;
#
# 2. I Am Unable To Translate The 2 Files "UpButton.png" And "DownButton.png"
#    Using "img2py" (Under wx.tools) Or With PIL In Order To Embed Them In
#    A Python File. Every Translation I Made, Did Not Preserve The Alpha
#    Channel So I Ended Up With Round Buttons Inside Black Squares. Does
#    Anyone Have A Suggestion Here?
#
# 3. Creating *A Lot* Of ShapedButtons May Require Some Time. In The Demo,
#    I Create 23 Buttons In About 0.4 Seconds On Windows XP, 3 GHz 1 GB RAM.
#
# 4. Creating Buttons With Size Greater Than wx.Size(200, 200) May Display
#    Buttons With Clearly Evident Pixel Edges. This Is Due To The Size Of The
#    Image Files I Load During Initialization. If This Is Not Satisfactory,
#    Please Let Me Know And I Will Upload Bigger Files.
#
# For All Kind Of Problems, Requests Of Enhancements And Bug Reports, Please
# Write To Me At:
#
# andrea.gavana@agip.it
# andrea_gavan@tin.it
#
# Or, Obviously, To The wxPython Mailing List!!!
#
#
# End Of Comments
# --------------------------------------------------------------------------- #


"""Description:

ShapedButton Tries To Fill The Lack Of "Custom Shaped" Controls In wxPython
(That Depends On The Same Lack In wxWidgets). It Can Be Used To Build Round
Buttons Or Elliptic Buttons.

I Have Stolen Some Code From wx.lib.buttons In Order To Recreate The Same
Classes (GenButton, GenBitmapButton, GenBitmapTextButton, GenToggleButton,
GenBitmapToggleButton, GenBitmapTextToggleButton). Here You Have The Same
Classes (With "Gen" Replaced By "S"), With The Same Event Handling, But They
Are Rounded/Elliptical Buttons.

ShapedButton Is Based On A wx.Window, In Which 2 Images Are Drawn Depending
On The Button State (Pressed Or Not Pressed). The 2 Images Have Been Stolen
From Audacity (Written With wxWidgets) And Rearranged/Reshaped/Restyled
Using Adobe Photoshop.
Changing The Button Colour In Runtime Was More Difficult, But Using Some
Intelligent Instruction From The PIL Library It Can Be Done.

ShapedButton Reacts On Mouse Events *Only* If The Mouse Event Occurred Inside
The Circle/Ellipse, Even If ShapedButton Is Built On A Rectangular Window.
This Behavior Is A Lot Different With Respect To Audacity Round Buttons.


Usage:

The ShapedButton Constructions, Excluding wxPython Parameter Are, For The
6 Classes:

MyShapedButton = SButton(parent,
                         label)

MyShapedButton = SBitmapButton(parent,
                               bitmap)

MyShapedButton = SBitmapTextButton(parent,
                                   bitmap,
                                   label)

MyShapedButton = SToggleButton(parent,
                               label)

MyShapedButton = SBitmapToggleButton(parent,
                                     bitmap)

MyShapedButton = SBitmapTextToggleButton(parent,
                                         bitmap,
                                         label)

The ShapedButton Construction And Usage Is Quite Similar To The wx.lib.buttons
Implementation.
For The Full Listing Of The Input Parameters, See The ShapedButton __init__()
Method.


Methods And Settings:

With ShapedButton You Can:

- Create Rounded/Elliptical Buttons/ToggleButtons;
- Set Images For The Enabled/Disabled/Focused/Selected State Of The Button;
- Draw The Focus Indicator (Or Disable It);
- Set Label Colour And Font;
- Apply A Rotation To The ShapedButton Label;
- Change ShapedButton Shape And Text Orientation In Runtime.

For More Info On Methods And Initial Styles, Please Refer To The __init__()
Method For ShapedButton Or To The Specific Functions.

|=========================================================================== |
| NOTE: Shaped Button *Requires* The PIL (Python Imaging Library) Library To |
|       Be Installed.                                                        |
|=========================================================================== |


ShapedButton Control Is Freeware And Distributed Under The wxPython License. 

Latest Revision: Andrea Gavana @ 18 Oct 2005, 21.50 CET

"""


#----------------------------------------------------------------------
# Beginning Of SHAPEDBUTTON wxPython Code
#----------------------------------------------------------------------

import wx
from wx.lib import imageutils

# First Check If PIL Is Installed Properly
try:

    import Image
    
except ImportError:
    
    errstr = ("\nShapedButton *Requires* PIL (Python Imaging Library).\n"
             "You Can Get It At:\n\n"
             "http://www.pythonware.com/products/pil/\n\n"
             "ShapedButton Can Not Continue. Exiting...\n")
    
    raise errstr

import os

# Import Some Stuff For The Annoying Ellipsis... ;-)
from math import sin, cos, pi


#-----------------------------------------------------------------------------
# PATH & FILE FILLING FUNCTION (OS INDEPENDENT)
# This Is Required To Load The Pressed And Non-Pressed Images From The
# "images" Directory.
#-----------------------------------------------------------------------------

def opj(path):
    """Convert Paths To The Platform-Specific Separator"""
    
    str = apply(os.path.join, tuple(path.split('/')))
    # HACK: on Linux, a leading / gets lost...
    if path.startswith('/'):
        str = '/' + str
        
    return str

#-----------------------------------------------------------------------------


#----------------------------------------------------------------------
# Class SButtonEvent
# Code Stolen From wx.lib.buttons. This Class Handles All The Button
# And ToggleButton Events.
#----------------------------------------------------------------------

class SButtonEvent(wx.PyCommandEvent):
    """Event Sent From The Generic Buttons When The Button Is Activated. """
    
    def __init__(self, eventType, ID):
        wx.PyCommandEvent.__init__(self, eventType, ID)
        self.isDown = False
        self.theButton = None

    def SetIsDown(self, isDown):
        self.isDown = isDown

    def GetIsDown(self):
        return self.isDown

    def SetButtonObj(self, btn):
        self.theButton = btn

    def GetButtonObj(self):
        return self.theButton


#----------------------------------------------------------------------
# SBUTTON Class
# This Is The Main Class Implementation. See __init__() Method For
# Details. All The Other Button Types Depend On This Class For Event
# Handling And Property Settings.
#----------------------------------------------------------------------

class SButton(wx.Window):

    _labeldelta = 1
    
    def __init__(self, parent, id=wx.ID_ANY,label="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        """ Default Class Constructor.

        Non Standard wxPython Parameters Are:

        a) label: The Label You Wish To Assing To Your SButton.

        """
        
        wx.Window.__init__(self, parent, id, pos, size)

        if label is None:
            label = ""

        self._enabled = True

        # It Is Impossible To Correctly Transform These Images Into Python
        # Files Without Losing Transparency
        upfile = opj("images/UpButton.png")
        downfile = opj("images/DownButton.png")
        
        self._originalup = Image.open(upfile, "r")
        self._originaldown = Image.open(downfile, "r")
        
        self._isup = True
        self._hasfocus = False
        self._usefocusind = True

        # Initialize Button Properties
        self.SetButtonColour()
        self.SetLabel(label)
        self.SetLabelColour()
        self.InitColours()
        self.SetAngleOfRotation()
        self.SetEllipseAxis()

        if size == wx.DefaultSize:
            self.SetBestFittingSize(self.DoGetBestSize())

        # Event Binding
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        
        if wx.Platform == '__WXMSW__':
            self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDown)
            
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SET_FOCUS, self.OnGainFocus)
        self.Bind(wx.EVT_KILL_FOCUS, self.OnLoseFocus)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)

        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)        
        self.Bind(wx.EVT_PAINT, self.OnPaint)


    def SetButtonColour(self, colour=None):
        """ Sets The Button Colour, For All Button States.

        The Original Button Images Are GreyScale With A Lot Of Pixels With
        Different Colours. Changing Smoothly The Button Colour In Order To
        Give The Same 3D Effect Can Be Efficiently Done Only With PIL.
        """

        if colour is None:
            colour = wx.WHITE

        palette = colour.Red(), colour.Green(), colour.Blue()
            
        self._buttoncolour = colour

        # Change The Pressed Button First
        img = self._originaldown
        l = self.MakePalette(*palette)
        # The Palette Can Be Applied Only To "L" And "P" Images, Not "RGBA"
        img = img.convert("L")
        # Apply The New Palette
        img.putpalette(l)
        # Convert The Image Back To RGBA
        img = img.convert("RGBA")
        self._mainbuttondown = self.ConvertPILToWX(img)

        # Now Is The Non Pressed Button Time
        img = self._originalup
        img = img.convert("L")
        img.putpalette(l)
        img = img.convert("RGBA")
        self._mainbuttonup = self.ConvertPILToWX(img)


    def GetButtonColour(self):
        """ Returns The Button Colour."""
        
        return self._buttoncolour


    def SetLabelColour(self, colour=None):
        """ Sets The Button Label Colour."""
        
        if colour is None:
            colour = wx.BLACK
            
        self._labelcolour = colour        


    def GetLabelColour(self):
        """ Returns The Button Label Colour."""
        
        return self._labelcolour
    

    def SetLabel(self, label=None):
        """ Sets The Button Label."""
        
        if label is None:
            label = ""

        self._buttonlabel = label


    def GetLabel(self):
        """ Returns The Button Label."""
        
        return self._buttonlabel


    def SetBestSize(self, size=None):
        """ Given The Current Font Settings, Calculate And Set A Good Size. """
        
        if size is None:
            size = wx.DefaultSize
            
        self.SetBestFittingSize(size)


    def DoGetBestSize(self):
        """
        Overridden Base Class Virtual. Determines The Best Size Of The Button
        Based On The Label Size.
        """
        
        w, h, usemin = self._GetLabelSize()
        defsize = wx.Button.GetDefaultSize()
        width = 12 + w
        
        if usemin and width < defsize.width:
           width = defsize.width
           
        height = 11 + h
        
        if usemin and height < defsize.height:
            height = defsize.height
            
        return (width, height)
    

    def AcceptsFocus(self):
        """ Overridden Base Class Virtual. """
        
        return self.IsShown() and self.IsEnabled()


    def ShouldInheritColours(self):
        """
        Overridden Base Class Virtual.  Buttons Usually Don't Inherit The
        Parent's Colours.
        """
        
        return False
    

    def Enable(self, enable=True):
        """ Enables/Disables The Button. """
        
        self._enabled = enable
        self.Refresh()


    def IsEnabled(self):
        """ Returns Wheter The Button Is Enabled Or Not. """
        
        return self._enabled
    

    def SetUseFocusIndicator(self, flag):
        """ Specifies If A Focus Indicator (Dotted Line) Should Be Used. """
        
        self._usefocusind = flag
        

    def GetUseFocusIndicator(self):
        """ Returns Focus Indicator Flag. """
        
        return self._usefocusind


    def InitColours(self):
        """
        Calculates A New Set Of Focus Indicator Colour And Indicator Pen
        Based On Button Colour And Label Colour.
        """
        
        textclr = self.GetLabelColour()
        faceclr = self.GetButtonColour()
        
        r, g, b = faceclr.Get()
        hr, hg, hb = min(255,r+64), min(255,g+64), min(255,b+64)
        self._focusclr = wx.Colour(hr, hg, hb)
        
        if wx.Platform == "__WXMAC__":
            self._focusindpen = wx.Pen(textclr, 1, wx.SOLID)
        else:
            self._focusindpen = wx.Pen(textclr, 1, wx.USER_DASH)
            self._focusindpen.SetDashes([1,1])
            self._focusindpen.SetCap(wx.CAP_BUTT)
        

    def SetDefault(self):
        """ Sets The Button As Default Item. """
        
        self.GetParent().SetDefaultItem(self)

        
    def _GetLabelSize(self):
        """ Used Internally """
        
        w, h = self.GetTextExtent(self.GetLabel())
        return w, h, True


    def Notify(self):
        """ Notifies An Event And Let It Be Processed. """
        
        evt = SButtonEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED, self.GetId())
        evt.SetIsDown(not self._isup)
        evt.SetButtonObj(self)
        evt.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(evt)


    def DrawMainButton(self, dc, width, height):
        """ Draws The Main Button, In Whichever State It Is. """
        
        w = min(width, height)
        
        position = self.GetPosition()

        main, secondary = self.GetEllipseAxis()
        xc = width/2
        yc = height/2
        
        if abs(main - secondary) < 1e-6:
            # In This Case The Button Is A Circle
            if self._isup:
                img = self._mainbuttonup.Scale(w, w)
            else:
                img = self._mainbuttondown.Scale(w, w)
        else:
            # In This Case The Button Is An Ellipse... Some Math To Do
            rect = self.GetRect()
            
            if main > secondary:
                # This Is An Ellipse With Main Axis Aligned With X Axis
                rect2 = w
                rect3 = w*secondary/main
                
            else:
                # This Is An Ellipse With Main Axis Aligned With Y Axis
                rect3 = w
                rect2 = w*main/secondary
                
            if self._isup:
                img = self._mainbuttonup.Scale(rect2, rect3)
            else:
                img = self._mainbuttondown.Scale(rect2, rect3)

        bmp = img.ConvertToBitmap()

        if abs(main - secondary) < 1e-6:
            if height > width:
                xpos = 0
                ypos = (height - width)/2
            else:
                xpos = (width - height)/2
                ypos = 0
        else:
            if height > width:
                if main > secondary:
                    xpos = 0
                    ypos = (height - rect3)/2
                else:
                    xpos = (width - rect2)/2
                    ypos = (height - rect3)/2
            else:
                if main > secondary:
                    xpos = (width - rect2)/2
                    ypos = (height - rect3)/2
                else:
                    xpos = (width - rect2)/2
                    ypos = 0

        # Draw Finally The Bitmap
        dc.DrawBitmap(bmp, xpos, ypos, True)

        # Store Bitmap Position And Size To Draw An Elliptical Focus Indicator
        self._xpos = xpos
        self._ypos = ypos
        self._imgx = img.GetWidth()
        self._imgy = img.GetHeight()
        
        
    def DrawLabel(self, dc, width, height, dw=0, dh=0):
        """ Draws The Label On The Button. """
        
        dc.SetFont(self.GetFont())

        if self.IsEnabled():
            dc.SetTextForeground(self.GetLabelColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))
            
        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label)
        
        w = min(width, height)

        # labeldelta Is Used To Give The Impression Of A "3D" Click        
        if not self._isup:
            dw = dh = self._labeldelta

        angle = self.GetAngleOfRotation()*pi/180.0

        # Check If There Is Any Rotation Chosen By The User
        if angle == 0:
            dc.DrawText(label, (width-tw)/2+dw, (height-th)/2+dh)
        else:
            xc, yc = (width/2, height/2)
            
            xp = xc - (tw/2)* cos(angle) - (th/2)*sin(angle)
            yp = yc + (tw/2)*sin(angle) - (th/2)*cos(angle)

            dc.DrawRotatedText(label, xp + dw, yp + dh , angle*180/pi)


    def DrawFocusIndicator(self, dc, width, height):
        """
        Draws The Focus Indicator. This Is A Circle/Ellipse Inside The Button
        Drawn With A Dotted-Style Pen, To Let The User Know Which Button Has
        The Focus.
        """
        
        self._focusindpen.SetColour(self._focusclr)
        dc.SetLogicalFunction(wx.INVERT)
        dc.SetPen(self._focusindpen)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        main, secondary = self.GetEllipseAxis()

        if abs(main - secondary) < 1e-6:
            # Ah, That Is A Round Button
            if height > width:
                dc.DrawCircle(width/2, height/2, width/2-4)
            else:
                dc.DrawCircle(width/2, height/2, height/2-4)
        else:
            # This Is An Ellipse
            if hasattr(self, "_xpos"):
                dc.DrawEllipse(self._xpos + 2, self._ypos + 2, self._imgx - 4, self._imgy - 4)
            
        dc.SetLogicalFunction(wx.COPY)


    def OnSize(self, event):
        """ Handles wx.EVT_SIZE Events. Mandatory On Windows (MSW)."""
        
        self.Refresh()
        event.Skip()
        

    def OnPaint(self, event):
        """ Handles The wx.EVT_PAINT Event. Mandatory On All Platforms. """
        
        (width, height) = self.GetClientSizeTuple()

        # Use A Double Buffered DC (Good Speed Up)
        dc = wx.BufferedPaintDC(self)

        # The DC Background *Must* Be The Same As The Parent Background Colour,
        # In Order To Hide The Fact That Our "Shaped" Button Is Still Constructed
        # Over A Rectangular Window
        brush = wx.Brush(self.GetParent().GetBackgroundColour(), wx.SOLID)
            
        dc.SetBackground(brush)
        dc.Clear()

        self.DrawMainButton(dc, width, height)                    
        self.DrawLabel(dc, width, height)

        if self._hasfocus and self._usefocusind:
            self.DrawFocusIndicator(dc, width, height)


    def IsOutside(self, x, y):
        """ Checks If A Mouse Events Occurred Inside The Circle/Ellipse Or Not. """

        (width, height) = self.GetClientSizeTuple()
        diam = min(width, height)
        xc, yc = (width/2, height/2)

        main, secondary = self.GetEllipseAxis()

        if abs(main - secondary) < 1e-6:
            # This Is A Circle
            if ((x - xc)**2.0 + (y - yc)**2.0) > (diam/2.0)**2.0:
                return True
        else:
            # This Is An Ellipse
            mn = max(main, secondary)
            main = self._imgx/2.0
            secondary = self._imgy/2.0
            if (((x-xc)/main)**2.0 + ((y-yc)/secondary)**2.0) > 1:
                return True

        return False
    
        
    def OnLeftDown(self, event):
        """ Handles Left Down Mouse Events. """

        if not self.IsEnabled():
            return

        x, y = (event.GetX(), event.GetY())

        if self.IsOutside(x,y):
            return
        
        self._isup = False
        self.CaptureMouse()
        self.SetFocus()

        self.Refresh()
        event.Skip()


    def OnLeftUp(self, event):
        """ Handles Left Up Mouse Events. """
        
        if not self.IsEnabled() or not self.HasCapture():
            return
        
        if self.HasCapture():
            self.ReleaseMouse()
            
            if not self._isup:
                self.Notify()
                
            self._isup = True
            self.Refresh()
            event.Skip()


    def OnMotion(self, event):
        """ Handles Mouse Motion Events. """
        
        if not self.IsEnabled() or not self.HasCapture():
            return
        
        if event.LeftIsDown() and self.HasCapture():
            x, y = event.GetPositionTuple()
            
            if self._isup and not self.IsOutside(x, y):
                self._isup = False
                self.Refresh()
                return
            
            if not self._isup and self.IsOutside(x,y):
                self._isup = True
                self.Refresh()
                return
            
        event.Skip()


    def OnGainFocus(self, event):
        """ Handles wx.EVT_SET_FOCUS Events. """
        
        self._hasfocus = True
        dc = wx.ClientDC(self)
        w, h = self.GetClientSizeTuple()
        
        if self._usefocusind:
            self.DrawFocusIndicator(dc, w, h)


    def OnLoseFocus(self, event):
        """ Handles wx.EVT_KILL_FOCUS Events. """
        
        self._hasfocus = False
        dc = wx.ClientDC(self)
        w, h = self.GetClientSizeTuple()
        
        if self._usefocusind:
            self.DrawFocusIndicator(dc, w, h)

        self.Refresh()


    def OnKeyDown(self, event):
        """ Handles Key Down Events Just Like wx.lib.buttons Do. """
        
        if self._hasfocus and event.KeyCode() == ord(" "):
            
            self._isup = False
            self.Refresh()
            
        event.Skip()


    def OnKeyUp(self, event):
        """ Handles Key Up Events Just Like wx.lib.buttons Do. """
        
        if self._hasfocus and event.KeyCode() == ord(" "):
            
            self._isup = True
            self.Notify()
            self.Refresh()
            
        event.Skip()

        
    def MakePalette(self, tr, tg, tb):
        """ Creates A Palette To Be Applied On An Image Based On Input Colour. """
        
        l = []
        for i in range(255):
            l.extend([tr*i / 255, tg*i / 255, tb*i / 255])
            
        return l


    def ConvertWXToPIL(self, bmp):
        """ Convert wx.Image Into PIL Image. """
        
        width = bmp.GetWidth()
        height = bmp.GetHeight()
        img = Image.fromstring("RGBA", (width, height), bmp.GetData())

        return img


    def ConvertPILToWX(self, pil, alpha=True):
        """ Convert PIL Image Into wx.Image. """
        
        if alpha:
            image = apply(wx.EmptyImage, pil.size)
            image.SetData( pil.convert("RGB").tostring() )
            image.SetAlphaData(pil.convert("RGBA").tostring()[3::4])
        else:
            image = wx.EmptyImage(pil.size[0], pil.size[1])
            new_image = pil.convert('RGB')
            data = new_image.tostring()
            image.SetData(data)
           
        return image


    def SetAngleOfRotation(self, angle=None):
        """ Sets Angle Of Button Label Rotation (In Degrees!!). """

        if angle is None:
            angle = 0

        self._rotation = angle*pi/180


    def GetAngleOfRotation(self):
        """ Returns Angle Of Button Label Rotation (In Degrees!!). """

        return self._rotation*180.0/pi


    def SetEllipseAxis(self, main=None, secondary=None):
        """
        Sets The Ellipse Axis. What It Is Important Is Not Their Absolute Values
        But Their Ratio.
        """

        if main is None:
            main = 1.0
            secondary = 1.0

        self._ellipseaxis = (main, secondary)


    def GetEllipseAxis(self):
        """ Returns The Ellipse Axis. """
        
        return self._ellipseaxis        
    

#----------------------------------------------------------------------
# SBITMAPBUTTON Class
# It Is Derived From SButton, And It Is A Class Useful To Draw A
# ShapedButton With An Image In The Middle. The Button Can Have 4
# Different Bitmaps Assigned To Its Different States (Pressed, Non
# Pressed, With Focus, Disabled.
#----------------------------------------------------------------------


class SBitmapButton(SButton):

    def __init__(self, parent, id, bitmap,
                 pos = wx.DefaultPosition, size = wx.DefaultSize):
        """ Default Class Constructor.

        Non Standard wxPython Parameters Are:

        a) bitmap: The bitmap You Wish To Assing To Your SBitmapButton.

        """
        
        self._bmpdisabled = None
        self._bmpfocus = None
        self._bmpselected = None
        
        self.SetBitmapLabel(bitmap)
        
        SButton.__init__(self, parent, id, "", pos, size)


    def GetBitmapLabel(self):
        return self._bmplabel

    
    def GetBitmapDisabled(self):
        """ Returns The Bitmap Displayed When The Button Is Disabled. """
        
        return self._bmpdisabled

    
    def GetBitmapFocus(self):
        """ Returns The Bitmap Displayed When The Button Has The Focus. """
        
        return self._bmpfocus

    
    def GetBitmapSelected(self):
        """ Returns The Bitmap Displayed When The Button Is Selected (Pressed). """
        
        return self._bmpselected


    def SetBitmapDisabled(self, bitmap):
        """ Sets The Bitmap To Display When The Button Is Disabled. """
        
        self._bmpdisabled = bitmap


    def SetBitmapFocus(self, bitmap):
        """ Sets The Bitmap To Display When The Button Has The Focus. """
        
        self._bmpfocus = bitmap
        self.SetUseFocusIndicator(False)
        

    def SetBitmapSelected(self, bitmap):
        """ Sets The Bitmap To Display When The Button Is Selected (Pressed). """
        
        self._bmpselected = bitmap
        

    def SetBitmapLabel(self, bitmap, createothers=True):
        """
        Sets The Bitmap To Display Normally. This Is The Only One That Is
        Required. If "createothers" Is True, Then The Other Bitmaps Will
        Be Generated On The Fly. Currently, Only The Disabled Bitmap Is
        Generated.
        """
        
        self._bmplabel = bitmap
        
        if bitmap is not None and createothers:
            image = wx.ImageFromBitmap(bitmap)
            imageutils.grayOut(image)
            self.SetBitmapDisabled(wx.BitmapFromImage(image))


    def _GetLabelSize(self):
        """ Used Internally """
        
        if not self._bmplabel:
            return -1, -1, False
        
        return self._bmplabel.GetWidth() + 2, self._bmplabel.GetHeight() + 2, False


    def DrawLabel(self, dc, width, height, dw=0, dh=0):
        """ Draws The Bitmap In The Middle Of The Button. """
        
        bmp = self._bmplabel
        
        if self._bmpdisabled and not self.IsEnabled():
            bmp = self._bmpdisabled
            
        if self._bmpfocus and self._hasfocus:
            bmp = self._bmpfocus
            
        if self._bmpselected and not self._isup:
            bmp = self._bmpselected
            
        bw, bh = bmp.GetWidth(), bmp.GetHeight()

        if not self._isup:
            dw = dh = self._labeldelta
            
        hasMask = bmp.GetMask() != None
        dc.DrawBitmap(bmp, (width - bw)/2 + dw, (height - bh)/2 + dh, hasMask)


#----------------------------------------------------------------------
# SBITMAPTEXTBUTTON Class
# It Is Derived From SButton, And It Is A Class Useful To Draw A
# ShapedButton With An Image And Some Text Ceneterd In The Middle.
# The Button Can Have 4 Different Bitmaps Assigned To Its Different
# States (Pressed, Non Pressed, With Focus, Disabled.
#----------------------------------------------------------------------

class SBitmapTextButton(SBitmapButton):
    
    def __init__(self, parent, id, bitmap, label,
                 pos = wx.DefaultPosition, size = wx.DefaultSize):

        """ Default Class Constructor.

        Non Standard wxPython Parameters Are:

        a) bitmap: The bitmap You Wish To Assing To Your SBitmapTextButton;
        b) label: The Text That Will Be Displayed Together With The bitmap.

        """
        
        SBitmapButton.__init__(self, parent, id, bitmap, pos, size)
        self.SetLabel(label)


    def _GetLabelSize(self):
        """ Used Internally """
        
        w, h = self.GetTextExtent(self.GetLabel())
        
        if not self._bmplabel:
            return w, h, True       # if there isn't a bitmap use the size of the text

        w_bmp = self._bmplabel.GetWidth() + 2
        h_bmp = self._bmplabel.GetHeight() + 2
        width = w + w_bmp
        
        if h_bmp > h:
            height = h_bmp
        else:
            height = h
            
        return width, height, True


    def DrawLabel(self, dc, width, height, dw=0, dh=0):
        """ Draws The Bitmap And The Text Labels. """
        
        bmp = self._bmplabel
        
        if bmp != None:     # if the bitmap is used
            
            if self._bmpdisabled and not self.IsEnabled():
                bmp = self._bmpdisabled
                
            if self._bmpfocus and self._hasfocus:
                bmp = self._bmpfocus
                
            if self._bmpselected and not self._isup:
                bmp = self._bmpselected
                
            bw, bh = bmp.GetWidth(), bmp.GetHeight()
            
            if not self._isup:
                dw = dh = self._labeldelta
                
            hasMask = bmp.GetMask() != None
            
        else:
            
            bw = bh = 0     # no bitmap -> size is zero

        dc.SetFont(self.GetFont())
        
        if self.IsEnabled():
            dc.SetTextForeground(self.GetLabelColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label)  # size of text
        
        if not self._isup:
            dw = dh = self._labeldelta

        w = min(width, height)
        
        pos_x = (width - bw - tw)/2 + dw      # adjust for bitmap and text to centre

        rotangle = self.GetAngleOfRotation()*pi/180.0
        
        if bmp != None:
            if rotangle < 1.0/180.0:
                dc.DrawBitmap(bmp, pos_x, (height - bh)/2 + dh, hasMask) # draw bitmap if available
                pos_x = pos_x + 4   # extra spacing from bitmap
            else:
                pass

        if rotangle < 1.0/180.0:
            dc.DrawText(label, pos_x + dw + bw, (height-th)/2+dh)      # draw the text
        else:
            xc, yc = (width/2, height/2)
            xp = xc - (tw/2)* cos(rotangle) - (th/2)*sin(rotangle)
            yp = yc + (tw/2)*sin(rotangle) - (th/2)*cos(rotangle)
            dc.DrawRotatedText(label, xp, yp , rotangle*180.0/pi)


#----------------------------------------------------------------------
# __STOGGLEMIXIN Class
# A Mixin That Allows To Transform Any Of SButton, SBitmapButton And
# SBitmapTextButton In The Corresponding ToggleButtons.
#----------------------------------------------------------------------

class __SToggleMixin:


    def SetToggle(self, flag):
        
        self._isup = not flag
        self.Refresh()
        
    SetValue = SetToggle


    def GetToggle(self):
        
        return not self._isup
    
    GetValue = GetToggle


    def OnLeftDown(self, event):
        
        if not self.IsEnabled():
            return

        x, y = (event.GetX(), event.GetY())

        if self.IsOutside(x,y):
            return        
        
        self._saveup = self._isup
        self._isup = not self._isup
        self.CaptureMouse()
        self.SetFocus()
        self.Refresh()


    def OnLeftUp(self, event):
        
        if not self.IsEnabled() or not self.HasCapture():
            return
        
        if self.HasCapture():
            if self._isup != self._saveup:
                self.Notify()
                
            self.ReleaseMouse()
            self.Refresh()
            

    def OnKeyDown(self, event):
        
        event.Skip()


    def OnMotion(self, event):
        
        if not self.IsEnabled():
            return
        
        if event.LeftIsDown() and self.HasCapture():
            
            x,y = event.GetPositionTuple()
            w,h = self.GetClientSizeTuple()

            if not self.IsOutside(x, y):
                self._isup = not self._saveup
                self.Refresh()
                return
            
            if self.IsOutside(x,y):
                self._isup = self._saveup
                self.Refresh()
                return
            
        event.Skip()


    def OnKeyUp(self, event):
        
        if self._hasfocus and event.KeyCode() == ord(" "):
            
            self._isup = not self._isup
            self.Notify()
            self.Refresh()
            
        event.Skip()


#----------------------------------------------------------------------
# STOGGLEBUTTON Class
#----------------------------------------------------------------------

class SToggleButton(__SToggleMixin, SButton):
    """ A ShapedButton Toggle Button. """
    pass


#----------------------------------------------------------------------
# SBITMAPTOGGLEBUTTON Class
#----------------------------------------------------------------------

class SBitmapToggleButton(__SToggleMixin, SBitmapButton):
    """ A ShapedButton Toggle Bitmap Button. """
    pass


#----------------------------------------------------------------------
# SBITMAPTEXTTOGGLEBUTTON Class
#----------------------------------------------------------------------

class SBitmapTextToggleButton(__SToggleMixin, SBitmapTextButton):
    """ A ShapedButton Toggle Bitmap Button With A Text Label. """
    pass



