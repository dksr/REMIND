""" sp_rels_gui

    Based on pySketch from wx demos.
    
    Known Bugs:
      ***** When a saved file is loaded, then you cannot move group of objects 
      using arrow keys. For this to work just press the change the tools and get 
      back to the selection tool and then move
      * Scrolling the window causes the drawing panel to be mucked up until you
        refresh it.  I've got no idea why.

      * I suspect that the reference counting for some wxPoint objects is
        getting mucked up; when the user quits, we get errors about being
        unable to call del on a 'None' object.

      * Saving files via pickling is not a robust cross-platform solution.
"""

import copy
import cPickle
import math
import matplotlib
import numpy as np
import os.path
import sys
import time
import traceback, types
import wx

from matplotlib.figure import Figure
from matplotlib.mlab import normpdf
from matplotlib.backends.backend_agg import FigureCanvasAgg
from numpy.random import randn
from pylab import linspace, meshgrid, sqrt
from wx.lib.buttons import GenBitmapButton,GenBitmapToggleButton

#matplotlib.use('WXAgg')
#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas

matplotlib.rcParams['xtick.direction'] = 'out'
matplotlib.rcParams['ytick.direction'] = 'out'


#----------------------------------------------------------------------------
#                            System Constants
#----------------------------------------------------------------------------

sys.setrecursionlimit(500)

# Our menu item IDs:

menu_DUPLICATE     = wx.NewId() # Edit menu items.
menu_GROUP         = wx.NewId()
menu_UNGROUP       = wx.NewId()
slider_TIMER       = wx.NewId()
redraw_TIMER       = wx.NewId()
menu_EDIT_PROPS    = wx.NewId()

menu_SELECT        = wx.NewId() # Tools menu items.
menu_RECT          = wx.NewId()

menu_DC            = wx.NewId() # View menu items.
menu_GCDC          = wx.NewId()

menu_MOVE_FORWARD  = wx.NewId() # Object menu items.
menu_MOVE_TO_FRONT = wx.NewId()
menu_MOVE_BACKWARD = wx.NewId()
menu_MOVE_TO_BACK  = wx.NewId()

menu_ORIENT_RIGHT = wx.NewId()
menu_ORIENT_LEFT  = wx.NewId()
menu_ORIENT_DOWN  = wx.NewId()
menu_ORIENT_UP    = wx.NewId()
menu_ORIENT_NONE  = wx.NewId()
menu_SET_AS_REF_OBJ = wx.NewId()

menu_ABOUT         = wx.NewId() # Help menu items.

# Our tool IDs:

id_SELECT   = wx.NewId()
id_RECT     = wx.NewId()

# Our tool option IDs:

id_FILL_OPT   = wx.NewId()
id_PEN_OPT    = wx.NewId()
id_LINE_OPT   = wx.NewId()
id_EDIT       = wx.NewId()

id_LINESIZE_0 = wx.NewId()
id_LINESIZE_1 = wx.NewId()
id_LINESIZE_2 = wx.NewId()
id_LINESIZE_3 = wx.NewId()
id_LINESIZE_4 = wx.NewId()
id_LINESIZE_5 = wx.NewId()

id_OBJTYPE_0 = wx.NewId()
id_OBJTYPE_1 = wx.NewId()
id_OBJTYPE_2 = wx.NewId()
id_OBJTYPE_3 = wx.NewId()
id_OBJTYPE_4 = wx.NewId()
id_OBJTYPE_5 = wx.NewId()
id_OBJTYPE_6 = wx.NewId()
id_OBJTYPE_7 = wx.NewId()
id_OBJTYPE_8 = wx.NewId()

INITIAL_FRAME = 1

# Size of the drawing page, in pixels.

PAGE_WIDTH  = 1000
PAGE_HEIGHT = 1000

def adjust_borders(fig, targets):
    "Translate desired pixel sizes into percentages based on figure size."
    dpi = fig.get_dpi()
    width, height = [float(v * dpi) for v in fig.get_size_inches()]
    conversions = {
        'top': lambda v: 1.0 - (v / height),
        'bottom': lambda v: v / height,
        'right': lambda v: 1.0 - (v / width),
        'left': lambda v: v / width,
        'hspace': lambda v: v / height,
        'wspace': lambda v: v / width,
        }
    opts = dict((k, conversions[k](v)) for k, v in targets.items())
    fig.subplots_adjust(**opts)
    
def adjust_spines(ax,spines):
    for loc, spine in ax.spines.iteritems():
        if loc in spines:
            spine.set_position(('outward',10)) # outward by 10 points
            spine.set_smart_bounds(True)
        else:
            spine.set_color('none') # don't draw spine

    # turn off ticks where there is no spine
    if 'left' in spines:
        ax.yaxis.set_ticks_position('left')
    else:
        # no yaxis ticks
        ax.yaxis.set_ticks([])

    if 'bottom' in spines:
        ax.xaxis.set_ticks_position('bottom')
    else:
        # no xaxis ticks
        ax.xaxis.set_ticks([])

def distance(x1, y1, x2, y2):
    # Calculates the length of a line in 2d space.
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))

def find_angle(x1,y1,x2,y2,x3,y3):
    a = distance(x1,y1,x2,y2)
    b = distance(x1,y1,x3,y3)
    c = distance(x2,y2,x3,y3)
    
    try:
        cos1 = (math.pow(a,2) + math.pow(b,2) - math.pow(c,2))/ (2 * a * b)        
    except ZeroDivisionError:
        cos1 = 1
    try:
        cos2 = (math.pow(a,2) + math.pow(c,2) - math.pow(b,2))/ (2 * a * c)
    except ZeroDivisionError:
        cos2 = 1
            
    ang1 = math.acos(round(cos1,2))
    ang2 = math.acos(round(cos2,2))
    ang = min(ang1, ang2)
    return ang

def gen_logistic(A, K, B, Q, M, t, v=0.5):
    num = K - A
    den = 1 + Q*(math.exp(-B*(t-M)))
    den = math.pow(den, 1/v)
    return A + num/den
        
#----------------------------------------------------------------------------

class DrawingFrame(wx.Frame):
    """ A frame showing the contents of a single document. """

    # ==========================================
    # == Initialisation and Window Management ==
    # ==========================================

    def __init__(self, parent, id, title, fileName=None):
        """ Standard constructor.

            'parent', 'id' and 'title' are all passed to the standard wx.Frame
            constructor.  'buffer = figurecanvas.tostring_rgb()

            fileName' is the name and path of a saved file to
            load into this frame, if any.
        """
        wx.Frame.__init__(self, parent, id, title,
                         style = wx.DEFAULT_FRAME_STYLE | wx.WANTS_CHARS |
                                 wx.NO_FULL_REPAINT_ON_RESIZE)

        self.ID_SLIDER = 1
        self.ID_STOP = 2
        self.ID_PLAY = 3
        self.ID_EDIT = 4
        self.ID_TIMER_PLAY = 5
        self.fps     = 5
        self.playing = False
        self.current_frame = 1
        self.edit = True
        
        self.core9_rels  = {}
        self.proj_rels   = {}
        self.obj_counter = 1
        self.group_counter = 1
        self.frame_data = {}
        self.groups = {}
        self.group_selection = []
        #self.frame_data[self.current_frame] = {'contents':[], 'selection':[], 'groups':[]}
        
        # Setup our menu bar.
        menuBar = wx.MenuBar()
          
        self.fileMenu = wx.Menu()
        self.fileMenu.Append(wx.ID_NEW,    "New\tCtrl-N", "Create a new document")
        self.fileMenu.Append(wx.ID_OPEN,   "Open...\tCtrl-O", "Open an existing document")
        self.fileMenu.Append(wx.ID_CLOSE,  "Close\tCtrl-W")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_SAVE,   "Save\tCtrl-S")
        self.fileMenu.Append(wx.ID_SAVEAS, "Save As...")
        self.fileMenu.Append(wx.ID_REVERT, "Revert...")
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT,   "Quit\tCtrl-Q")

        menuBar.Append(self.fileMenu, "File")

        self.editMenu = wx.Menu()
        self.editMenu.Append(wx.ID_UNDO,      "Undo\tCtrl-Z")
        self.editMenu.Append(wx.ID_REDO,      "Redo\tCtrl-Y")
        self.editMenu.AppendSeparator()
        self.editMenu.Append(wx.ID_SELECTALL, "Select All\tCtrl-A")
        self.editMenu.AppendSeparator()
        self.editMenu.Append(menu_DUPLICATE,  "Duplicate\tCtrl-D")
        self.editMenu.Append(menu_EDIT_PROPS,"Edit...\tCtrl-E", "Edit object properties")
        self.editMenu.Append(wx.ID_CLEAR,     "Delete\tDel")

        menuBar.Append(self.editMenu, "Edit")

        self.viewMenu = wx.Menu()
        self.viewMenu.Append(menu_DC,  "Normal quality", 
                             "Normal rendering using wx.DC",
                             kind=wx.ITEM_RADIO)
        self.viewMenu.Append(menu_GCDC,"High quality", 
                             "Anti-aliased rendering using wx.GCDC", 
                             kind=wx.ITEM_RADIO)

        menuBar.Append(self.viewMenu, "View")

        self.toolsMenu = wx.Menu()
        self.toolsMenu.Append(id_SELECT,  "Selection", kind=wx.ITEM_RADIO)
        self.toolsMenu.Append(id_RECT,    "Rectangle", kind=wx.ITEM_RADIO)
      
        menuBar.Append(self.toolsMenu, "Tools")

        self.objectMenu = wx.Menu()
        self.objectMenu.Append(menu_MOVE_FORWARD,  "Move Forward")
        self.objectMenu.Append(menu_MOVE_TO_FRONT, "Move to Front\tCtrl-F")
        self.objectMenu.Append(menu_MOVE_BACKWARD, "Move Backward")
        self.objectMenu.Append(menu_MOVE_TO_BACK,  "Move to Back\tCtrl-B")

        menuBar.Append(self.objectMenu, "Object")

        self.helpMenu = wx.Menu()
        self.helpMenu.Append(menu_ABOUT, "About pySketch...")

        menuBar.Append(self.helpMenu, "Help")

        self.SetMenuBar(menuBar)

        # Create our statusbar

        self.CreateStatusBar()

        # Create our toolbar.

        tsize = (15,15)
        self.toolbar = self.CreateToolBar(wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT)

        artBmp = wx.ArtProvider.GetBitmap
        self.toolbar.AddSimpleTool(
            wx.ID_NEW, artBmp(wx.ART_NEW, wx.ART_TOOLBAR, tsize), "New")
        self.toolbar.AddSimpleTool(
            wx.ID_OPEN, artBmp(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize), "Open")
        self.toolbar.AddSimpleTool(
            wx.ID_SAVE, artBmp(wx.ART_FILE_SAVE, wx.ART_TOOLBAR, tsize), "Save")
        self.toolbar.AddSimpleTool(
            wx.ID_SAVEAS, artBmp(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR, tsize),
            "Save As...")
        #-------
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(
            wx.ID_UNDO, artBmp(wx.ART_UNDO, wx.ART_TOOLBAR, tsize), "Undo")
        self.toolbar.AddSimpleTool(
            wx.ID_REDO, artBmp(wx.ART_REDO, wx.ART_TOOLBAR, tsize), "Redo")
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(
            menu_DUPLICATE, wx.Bitmap("images/duplicate.bmp", wx.BITMAP_TYPE_BMP),
            "Duplicate")\
        #-------
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(
            menu_MOVE_FORWARD, wx.Bitmap("images/moveForward.bmp", wx.BITMAP_TYPE_BMP),
            "Move Forward")
        self.toolbar.AddSimpleTool(
            menu_MOVE_BACKWARD, wx.Bitmap("images/moveBack.bmp", wx.BITMAP_TYPE_BMP),
            "Move Backward")
        
        self.toolbar.AddSeparator()
        self.slider = wx.Slider(self.toolbar, -1, 1, 1, 300, None, (500, 50), wx.SL_HORIZONTAL)
        self.toolbar.AddSeparator()
        self.play = self.toolbar.AddLabelTool(self.ID_PLAY, '', wx.Bitmap('images/play.png'))
        self.stop = self.toolbar.AddLabelTool(self.ID_STOP, '', wx.Bitmap('images/stop.png'))

        self.toolbar.AddControl(self.slider)
        
        self.toolbar.AddSeparator()

        self.edit_button = self.toolbar.AddLabelTool(self.ID_EDIT, '', wx.Bitmap('images/logo.bmp'))
        
        self.toolbar.Realize()

        self.playTimer = wx.Timer(self, slider_TIMER)
        self.Bind(wx.EVT_TIMER, self.onNextFrame, self.playTimer)
        
        self.Bind(wx.EVT_SLIDER, self.onSlider, self.slider)
        self.Bind(wx.EVT_TOOL, self.onStop, self.stop)
        self.Bind(wx.EVT_TOOL, self.onPlay, self.play)
        self.Bind(wx.EVT_TOOL, self.onEdit, self.edit_button)
        
        # Associate menu/toolbar items with their handlers.
        menuHandlers = [
        (wx.ID_NEW,    self.doNew),
        (wx.ID_OPEN,   self.doOpen),
        (wx.ID_CLOSE,  self.doClose),
        (wx.ID_SAVE,   self.doSave),
        (wx.ID_SAVEAS, self.doSaveAs),
        (wx.ID_REVERT, self.doRevert),
        (wx.ID_EXIT,   self.doExit),

        (wx.ID_UNDO,         self.doUndo),
        (wx.ID_REDO,         self.doRedo),
        (wx.ID_SELECTALL,    self.doSelectAll),
        (menu_DUPLICATE,     self.doDuplicate),
        (menu_GROUP,         self.doGroup),
        (menu_UNGROUP,       self.doUngroup),
        (menu_EDIT_PROPS,    self.doEditObject),
        (wx.ID_CLEAR,        self.doDelete),
        
        (id_SELECT,  self.onChooseTool, self.updChooseTool),
        (id_RECT,    self.onChooseTool, self.updChooseTool),
        
        (menu_DC,      self.doChooseQuality),
        (menu_GCDC,    self.doChooseQuality),

        (menu_MOVE_FORWARD,  self.doMoveForward),
        (menu_MOVE_TO_FRONT, self.doMoveToFront),
        (menu_MOVE_BACKWARD, self.doMoveBackward),
        (menu_MOVE_TO_BACK,  self.doMoveToBack),
        
        (menu_ORIENT_RIGHT, self.doOrientRight),
        (menu_ORIENT_LEFT,  self.doOrientLeft),
        (menu_ORIENT_DOWN,  self.doOrientDown),
        (menu_ORIENT_UP,    self.doOrientUp),
        (menu_ORIENT_NONE,  self.doOrientNone),
        (menu_SET_AS_REF_OBJ, self.doSetRefObj),

        (menu_ABOUT, self.doShowAbout)]
        for combo in menuHandlers:
            id, handler = combo[:2]
            self.Bind(wx.EVT_MENU, handler, id = id)
            if len(combo)>2:
                self.Bind(wx.EVT_UPDATE_UI, combo[2], id = id)
                
        # Install our own method to handle closing the window.  This allows us
        # to ask the user if he/she wants to save before closing the window, as
        # well as keeping track of which windows are currently open.

        self.Bind(wx.EVT_CLOSE, self.doClose)

        # Install our own method for handling keystrokes.  We use this to let
        # the user move the selected object(s) around using the arrow keys.

        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyEvent)

        # Setup our top-most panel.  This holds the entire contents of the
        # window, excluding the menu bar.

        self.topPanel = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
        
        # Setup our tool palette, with all our drawing tools and option icons.

        self.toolPalette = wx.BoxSizer(wx.VERTICAL)

        self.selectIcon  = ToolPaletteToggle(self.topPanel, id_SELECT,
                                           "select", "Selection Tool", mode=wx.ITEM_RADIO)
        self.rectIcon    = ToolPaletteToggle(self.topPanel, id_RECT,
                                           "rect", "Rectangle Tool", mode=wx.ITEM_RADIO)
      
        # Create the tools
        self.tools = {
            'select'  : (self.selectIcon,   SelectDrawingTool()),
            'rect'    : (self.rectIcon,     RectDrawingTool()),
        }


        toolSizer = wx.GridSizer(0, 2, 5, 5)
        toolSizer.Add(self.selectIcon)
        toolSizer.Add(self.rectIcon)

        self.optionIndicator = ToolOptionIndicator(self.topPanel)
        self.optionIndicator.SetToolTip(
                wx.ToolTip("Shows Current Pen/Fill/Line Size Settings"))

        optionSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.penOptIcon  = ToolPaletteButton(self.topPanel, id_PEN_OPT,
                                             "penOpt", "Set Pen Colour",)
        self.fillOptIcon = ToolPaletteButton(self.topPanel, id_FILL_OPT,
                                             "fillOpt", "Set Fill Colour")
        self.lineOptIcon = ToolPaletteButton(self.topPanel, id_LINE_OPT,
                                             "lineOpt", "Set Line Size")

        margin = wx.LEFT | wx.RIGHT
        optionSizer.Add(self.penOptIcon,  0, margin, 1)
        optionSizer.Add(self.fillOptIcon, 0, margin, 1)
        optionSizer.Add(self.lineOptIcon, 0, margin, 1)

        editSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.editOptIcon  = ToolPaletteButton(self.topPanel, id_EDIT,
                                             "lineOpt", "Set the obj type",)
        
        editSizer.Add(self.editOptIcon,  0, margin, 1)
        
        # By default the name of object is number, change it using the text field
        self.objName = wx.TextCtrl(self.topPanel, -1)
        self.objNameBtn = wx.Button(self.topPanel, -1,"ChangeName") 
        self.Bind(wx.EVT_BUTTON, self.changeObjName, id = self.objNameBtn.GetId()) 
        #self.some_text.SetLabel(mysql_data)
        self.objSize = wx.StaticText(self.topPanel, wx.ID_ANY, label="0 x 0", style=wx.ALIGN_CENTER)
        self.objPos  = wx.StaticText(self.topPanel, wx.ID_ANY, label="0 x 0", style=wx.ALIGN_CENTER)
        self.frameLabel = wx.StaticText(self.topPanel, wx.ID_ANY, label="1", style=wx.ALIGN_CENTER)
        
        objInfoSizer = wx.BoxSizer(wx.VERTICAL)
        objInfoSizer.Add(self.frameLabel, 0, margin, 3)        
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add(self.objSize, 0, margin, 3)
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add(self.objPos, 0, margin, 3)
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add(self.objName,    0, margin, 3)
        objInfoSizer.Add((0, 0), 0, margin, 5) # Spacer.
        objInfoSizer.Add(self.objNameBtn, 0, margin, 3)
        
        margin = wx.TOP | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTRE
        self.toolPalette.Add(toolSizer,            0, margin, 5)
        self.toolPalette.Add((0, 0),               0, margin, 5) # Spacer.
        self.toolPalette.Add(self.optionIndicator, 0, margin, 5)
        self.toolPalette.Add(optionSizer,          0, margin, 5)
        self.toolPalette.Add((0, 0),               0, margin, 5) # Spacer.
        self.toolPalette.Add(editSizer,            0, margin, 5)
        self.toolPalette.Add((0, 0),               0, margin, 5) # Spacer.
        self.toolPalette.Add((0, 0),               0, margin, 5) # Spacer.
        self.toolPalette.Add(objInfoSizer,         0, margin, 5)
        
        # Make the tool palette icons respond when the user clicks on them.

        for tool in self.tools.itervalues():
            tool[0].Bind(wx.EVT_BUTTON,    self.onChooseTool)

        self.selectIcon.Bind(wx.EVT_BUTTON, self.onChooseTool)
    
        self.penOptIcon.Bind(wx.EVT_BUTTON, self.onPenOptionIconClick)
        self.fillOptIcon.Bind(wx.EVT_BUTTON, self.onFillOptionIconClick)
        self.lineOptIcon.Bind(wx.EVT_BUTTON, self.onLineOptionIconClick)
        self.editOptIcon.Bind(wx.EVT_BUTTON, self.onEditOptionIconClick)

        # Setup the main drawing area.

        self.drawPanel = wx.ScrolledWindow(self.topPanel, -1,
                                          style=wx.SUNKEN_BORDER|wx.NO_FULL_REPAINT_ON_RESIZE)
        #self.infoPanel = wx.ScrolledWindow(self.topPanel, -1,
        #                                  style=wx.SUNKEN_BORDER|wx.NO_FULL_REPAINT_ON_RESIZE)
        self.infoPanel = wx.TextCtrl(self.topPanel, style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.infoPanel.Enable(0)
        self.infoPanel.SetEditable(False)
        
        gray_colour = wx.Colour(red=192, green=192, blue=192) 
        self.infoPanel.SetBackgroundColour(wx.BLACK) 
        dastyle = wx.TextAttr()
        #dastyle.SetBackgroundColour(wx.Colour(0,0,255))
        dastyle.SetTextColour(wx.Colour(255,255,255))
        points = self.infoPanel.GetFont().GetPointSize()
        bold_font = wx.Font(points+3, wx.ROMAN, wx.BOLD, True)
        dastyle.SetFont(bold_font)
        self.infoPanel.SetDefaultStyle(dastyle)
        
        self.drawPanel.SetBackgroundColour(gray_colour)
        
        self.drawPanel.EnableScrolling(True, True)
        #self.infoPanel.EnableScrolling(True, True)
        
        self.drawPanel.SetScrollbars(40, 40, PAGE_WIDTH / 40, PAGE_HEIGHT / 40)
        #self.infoPanel.SetScrollbars(20, 75, PAGE_WIDTH / 30, PAGE_HEIGHT / 30)

        self.drawPanel.Bind(wx.EVT_MOUSE_EVENTS, self.onMouseEvent)

        self.drawPanel.Bind(wx.EVT_IDLE, self.onIdle)
        self.drawPanel.Bind(wx.EVT_SIZE, self.onSize)
        self.drawPanel.Bind(wx.EVT_PAINT, self.onPaint)
        self.drawPanel.Bind(wx.EVT_ERASE_BACKGROUND, self.onEraseBackground)
        self.drawPanel.Bind(wx.EVT_SCROLLWIN, self.onPanelScroll)

        #self.Bind(wx.EVT_TIMER, self.onIdle)

        # Position everything in the window.
        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(self.toolPalette, 0)
        topSizer.Add(self.drawPanel, proportion=2, flag=wx.EXPAND)
        topSizer.Add(self.infoPanel, proportion=1, flag=wx.EXPAND)
        
        
        self.topPanel.SetAutoLayout(True)
        self.topPanel.SetSizer(topSizer)

        self.SetSizeHints(250, 200)
        self.SetSize(wx.Size(1800, 1200))

        # Select an initial tool.

        self.curToolName = None
        self.curToolIcon = None
        self.curTool = None
        self.setCurrentTool("select")

        # Set initial dc mode to fast
        self.wrapDC = lambda dc: dc

        # Setup our frame to hold the contents of a sketch document.

        self.dirty     = False
        self.fileName  = fileName
        self.contents  = []     # front-to-back ordered list of DrawingObjects.
        self.selection = []     # List of selected DrawingObjects.
        self.undoStack = []     # Stack of saved contents for undo.
        self.redoStack = []     # Stack of saved contents for redo.

        if self.fileName != None:
            self.loadContents()

        self._initBuffer()

        self._adjustMenus()

        # Finally, set our initial pen, fill and line options.

        self._setPenColour(wx.BLACK)
        self._setFillColour(wx.Colour(215,253,254))
        self._setLineSize(2)
        
        self.backgroundFillBrush = None # create on demand

        # Start the background redraw timer
        # This is optional, but it gives the double-buffered contents a 
        # chance to redraw even when idle events are disabled (like during 
        # resize and scrolling)
        self.redrawTimer = wx.Timer(self, redraw_TIMER)
        self.Bind(wx.EVT_TIMER, self.onIdle, self.redrawTimer)
        self.redrawTimer.Start(800)

    # ============================
    # == Event Handling Methods ==
    # ============================

    def changeObjName(self, event):
        """Change the object from default number to what ever entered in the text field"""
        objName = self.objName.GetValue() 
        # If more than one obj is selected, skip changing names. Only one obj must be selected.
        if len(self.selection) > 1:
            return
        self.selection[0].setName(objName.encode())
        self.requestRedraw()

    def onNextFrame(self, event):
        self.slider.SetValue(self.current_frame)
        self.frameLabel.SetLabel(repr(self.current_frame))
        if self.current_frame not in self.frame_data or self.edit:
            self.frame_data[self.current_frame] = self._buildStoredState()
        elif self.current_frame in self.frame_data and not self.edit:
            state = self.frame_data[self.current_frame]
            self._restoreStoredState(state)    
        self.current_frame += 1        

    def onEdit(self, event):
        if not self.edit:
            self.edit = True
        else:
            self.edit = False

    def onPlay(self, event):
        print 'PLAY'
        if not self.playing:
            self.playTimer.Start(100)
            self.playing = True
       
    def onStop(self, event):
        print 'STOP'
        if self.playing:
            self.playTimer.Stop()
            self.playing = False
    
    def onSlider(self, event):
        self.current_frame = self.slider.GetValue()
        #print self.current_frame
        if self.current_frame not in self.frame_data:
            self.frame_data[self.current_frame] = self._buildStoredState()
        else:
            state = self.frame_data[self.current_frame]
            self._restoreStoredState(state)

    def onEditOptionIconClick(self, event):
        """ Respond to the user clicking on the "Line Options" icon.
        """
        if len(self.selection) == 1:
            menu = self._buildObjTypePopup(self.selection[0].getObjType())
        else:
            menu = self._buildObjTypePopup(self.objType)

        pos = self.editOptIcon.GetPosition()
        pos.y = pos.y + self.lineOptIcon.GetSize().height
        self.PopupMenu(menu, pos)
        menu.Destroy()
        
    def onPenOptionIconClick(self, event):
        """ Respond to the user clicking on the "Pen Options" icon.
        """
        data = wx.ColourData()
        if len(self.selection) == 1:
            data.SetColour(self.selection[0].getPenColour())
        else:
            data.SetColour(self.penColour)

        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle('Choose line colour')
        if dialog.ShowModal() == wx.ID_OK:
            c = dialog.GetColourData().GetColour()
            self._setPenColour(wx.Colour(c.Red(), c.Green(), c.Blue()))
        dialog.Destroy()


    def onFillOptionIconClick(self, event):
        """ Respond to the user clicking on the "Fill Options" icon.
        """
        data = wx.ColourData()
        if len(self.selection) == 1:
            data.SetColour(self.selection[0].getFillColour())
        else:
            data.SetColour(self.fillColour)

        dialog = wx.ColourDialog(self, data)
        dialog.SetTitle('Choose fill colour')
        if dialog.ShowModal() == wx.ID_OK:
            c = dialog.GetColourData().GetColour()
            self._setFillColour(wx.Colour(c.Red(), c.Green(), c.Blue()))
        dialog.Destroy()

    def onLineOptionIconClick(self, event):
        """ Respond to the user clicking on the "Line Options" icon.
        """
        if len(self.selection) == 1:
            menu = self._buildLineSizePopup(self.selection[0].getLineSize())
        else:
            menu = self._buildLineSizePopup(self.lineSize)

        pos = self.lineOptIcon.GetPosition()
        pos.y = pos.y + self.lineOptIcon.GetSize().height
        self.PopupMenu(menu, pos)
        menu.Destroy()


    def onKeyEvent(self, event):
        """ Respond to a keypress event.

            We make the arrow keys move the selected object(s) by one pixel in
            the given direction.
        """
        step = 1
        if event.ShiftDown():
            step = 5

        if event.GetKeyCode() == wx.WXK_UP:
            self._moveObject(0, -step)
        elif event.GetKeyCode() == wx.WXK_DOWN:
            self._moveObject(0, step)
        elif event.GetKeyCode() == wx.WXK_LEFT:
            self._moveObject(-step, 0)
        elif event.GetKeyCode() == wx.WXK_RIGHT:
            self._moveObject(step, 0)
        else:
            event.Skip()


    def onMouseEvent(self, event):
        """ Respond to mouse events in the main drawing panel

            How we respond depends on the currently selected tool.
        """
        if self.curTool is None: return

        # Translate event into canvas coordinates and pass to current tool
        origx,origy = event.X, event.Y
        pt = self._getEventCoordinates(event)
        event.m_x = pt.x
        event.m_y = pt.y
        handled = self.curTool.onMouseEvent(self,event)
        event.m_x = origx
        event.m_y = origy

        if handled: return

        # otherwise handle it ourselves
        if event.RightDown():
            self.doPopupContextMenu(event)
        

    def doPopupContextMenu(self, event):
        """ Respond to the user right-clicking within our drawing panel.

            We select the clicked-on item, if necessary, and display a pop-up
            menu of available options which can be applied to the selected
            item(s).
        """
        mousePt = self._getEventCoordinates(event)
        obj = self.getObjectAt(mousePt)

        if obj == None: return # Nothing selected.
        
        # Select the clicked-on object.

        self.select(obj)

        # Build our pop-up menu.

        menu = wx.Menu()
        menu.Append(menu_DUPLICATE, "Duplicate")
        menu.Append(menu_GROUP, "Group")
        menu.Append(menu_UNGROUP, "Ungroup")
        menu.Append(menu_EDIT_PROPS,"Edit...")
        menu.Append(wx.ID_CLEAR,    "Delete")
        menu.AppendSeparator()
        menu.Append(menu_ORIENT_RIGHT, "Set orientation to RIGHT")
        menu.Append(menu_ORIENT_LEFT,  "Set orientation to LEFT")
        menu.Append(menu_ORIENT_DOWN,  "Set orientation to DOWN")
        menu.Append(menu_ORIENT_UP,    "Set orientation to UP")
        menu.Append(menu_ORIENT_NONE,    "Set orientation to None")
        menu.Append(menu_SET_AS_REF_OBJ, "Set/Unset as Reference Obj")
        menu.AppendSeparator()
        menu.Append(menu_MOVE_FORWARD,   "Move Forward")
        menu.Append(menu_MOVE_TO_FRONT,  "Move to Front")
        menu.Append(menu_MOVE_BACKWARD,  "Move Backward")
        menu.Append(menu_MOVE_TO_BACK,   "Move to Back")

        menu.Enable(menu_EDIT_PROPS,    obj.hasPropertyEditor())
        menu.Enable(menu_MOVE_FORWARD,  obj != self.contents[0])
        menu.Enable(menu_MOVE_TO_FRONT, obj != self.contents[0])
        menu.Enable(menu_MOVE_BACKWARD, obj != self.contents[-1])
        menu.Enable(menu_MOVE_TO_BACK,  obj != self.contents[-1])
        menu.Enable(menu_ORIENT_RIGHT,  obj.orientation != 'RIGHT')
        menu.Enable(menu_ORIENT_LEFT,   obj.orientation != 'LEFT')
        menu.Enable(menu_ORIENT_DOWN,   obj.orientation != 'DOWN')
        menu.Enable(menu_ORIENT_UP,     obj.orientation != 'UP')
        menu.Enable(menu_ORIENT_NONE,   obj.orientation != None)
        
        self.Bind(wx.EVT_MENU, self.doDuplicate,   id=menu_DUPLICATE)
        self.Bind(wx.EVT_MENU, self.doGroup,       id=menu_GROUP)
        self.Bind(wx.EVT_MENU, self.doUngroup,     id=menu_UNGROUP)
        self.Bind(wx.EVT_MENU, self.doEditObject,  id=menu_EDIT_PROPS)
        self.Bind(wx.EVT_MENU, self.doDelete,      id=wx.ID_CLEAR)
        self.Bind(wx.EVT_MENU, self.doMoveForward, id=menu_MOVE_FORWARD)
        self.Bind(wx.EVT_MENU, self.doMoveToFront, id=menu_MOVE_TO_FRONT)
        self.Bind(wx.EVT_MENU, self.doMoveBackward,id=menu_MOVE_BACKWARD)
        self.Bind(wx.EVT_MENU, self.doMoveToBack,  id=menu_MOVE_TO_BACK)
        self.Bind(wx.EVT_MENU, self.doOrientRight, id=menu_ORIENT_RIGHT)
        self.Bind(wx.EVT_MENU, self.doOrientLeft,  id=menu_ORIENT_LEFT)
        self.Bind(wx.EVT_MENU, self.doOrientDown,  id=menu_ORIENT_DOWN)
        self.Bind(wx.EVT_MENU, self.doOrientUp,    id=menu_ORIENT_UP)
        self.Bind(wx.EVT_MENU, self.doOrientNone,    id=menu_ORIENT_NONE)
        self.Bind(wx.EVT_MENU, self.doSetRefObj,   id=menu_SET_AS_REF_OBJ)

        # Show the pop-up menu.

        clickPt = wx.Point(mousePt.x + self.drawPanel.GetPosition().x,
                          mousePt.y + self.drawPanel.GetPosition().y)
        self.drawPanel.PopupMenu(menu, mousePt)
        menu.Destroy()


    def onSize(self, event):
        """
        Called when the window is resized.  We set a flag so the idle
        handler will resize the buffer.
        """
        self.requestRedraw()


    def onIdle(self, event):
        """
        If the size was changed then resize the bitmap used for double
        buffering to match the window size.  We do it in Idle time so
        there is only one refresh after resizing is done, not lots while
        it is happening.
        """
        if self._reInitBuffer:
            #print 'Compute the relations in onIdle'
            self.compute_spatial_rels()
            if self.IsShown():
                self._initBuffer()
                self.drawPanel.Refresh(False)

    def compute_spatial_rels(self):
        if len(self.contents) <= 1:
            self.infoPanel.Clear()
            return
        #core9_rels = {}
        for obj1 in self.contents:
            if obj1 not in self.selection:
                continue
            for obj2 in self.contents:
                if obj1.name == obj2.name:
                    continue
                self.core9_rels[(obj1.name, obj2.name)] = self.compute_core9_rel(obj1, obj2)
                self.core9_rels[(obj2.name, obj1.name)] = self.compute_core9_rel(obj2, obj1)
                self.proj_rels[(obj1.name, obj2.name)]  = self.compute_proj_rels(self.core9_rels[(obj1.name, obj2.name)], obj1.orientation)
                self.proj_rels[(obj2.name, obj1.name)]  = self.compute_proj_rels(self.core9_rels[(obj2.name, obj1.name)], obj2.orientation)
        
        display_text = self.get_rels_pretty_text(self.core9_rels, self.proj_rels)
        self.infoPanel.Clear()        
        self.infoPanel.Enable(1)
        
        self.infoPanel.SetInsertionPoint(0)
        self.infoPanel.WriteText(display_text)
        self.infoPanel.Enable(0)
    
    def get_rels_pretty_text(self, core9_rels_dict, proj_rels_dict):
        pretty_text = 'CORE-9\n'
        for key in core9_rels_dict:
            pretty_text += repr(key[0]) + ', ' + repr(key[1]) + ' : ' + '(' + \
                        core9_rels_dict[key][0] + ', ' + core9_rels_dict[key][1] + ')''\n'
            
        pretty_text += '\n-----------------------------------------------------------\n'    
        pretty_text += '\nProjective Relations\n'
        for key in proj_rels_dict:
            pretty_text += repr(key[0]) + ', ' + repr(key[1]) + ' : ' + proj_rels_dict[key] + '\n'
        return pretty_text
        
    def compute_proj_rels(self, (x_rel, y_rel), ref_obj_orientation):
        if ref_obj_orientation == 'DOWN' and x_rel != 'before' and x_rel != 'after' \
           and (y_rel == 'before' or y_rel == 'meets'):
            return 'in_front_of'
        elif ref_obj_orientation == 'UP' and x_rel != 'before' and x_rel != 'after' \
           and (y_rel == 'after' or y_rel == 'meets_i'):
            return 'in_front_of'
        elif ref_obj_orientation == 'RIGHT' and (x_rel == 'before' or x_rel == 'meets') \
           and (y_rel != 'before' and y_rel != 'after'):
            return 'in_front_of'
        elif ref_obj_orientation == 'LEFT' and (x_rel == 'after' or x_rel == 'meets_i') \
           and (y_rel != 'before' and y_rel != 'after'):
            return 'in_front_of'
        else:
            return 'NOT in_front_of'
        
    def compute_core9_rel(self, obj1, obj2):
        o1_xs, o1_xe = obj1.position.x, obj1.position.x + obj1.size.width
        o2_xs, o2_xe = obj2.position.x, obj2.position.x + obj2.size.width        
        
        o1_ys, o1_ye = obj1.position.y, obj1.position.y + obj1.size.height
        o2_ys, o2_ye = obj2.position.y, obj2.position.y + obj2.size.height        
        
        # In X-axis
        if o1_xe < o2_xs:
            x_rel = 'before'
        elif o2_xe < o1_xs:
            x_rel = 'after'
        elif o1_xe == o2_xs:
            x_rel = 'meets'
        elif o2_xe == o1_xs:
            x_rel = 'meets_i'    
        elif o1_xs == o2_xs and o1_xe < o2_xe:
            x_rel = 'starts'
        elif o1_xs == o2_xs and o1_xe > o2_xe:
            x_rel = 'starts_i'
        elif o1_xe == o2_xe and o1_xs > o2_xs:
            x_rel = 'finishes'
        elif o1_xe == o2_xe and o1_xs < o2_xs:
            x_rel = 'finishes_i'
        elif o1_xe == o2_xe and o1_xs == o2_xs:
            x_rel = 'equal'
        elif o1_xs > o2_xs and o1_xe < o2_xe:
            x_rel = 'during'
        elif o1_xs < o2_xs and o1_xe > o2_xe:
            x_rel = 'during_i'    
        elif o1_xs < o2_xs and o1_xe < o2_xe:
            x_rel = 'overlaps'
        elif o1_xs > o2_xs and o1_xe > o2_xe:
            x_rel = 'overlaps_i'
        
        # In Y-axis
        if o1_ye < o2_ys:
            y_rel = 'before'
        elif o2_ye < o1_ys:
            y_rel = 'after'
        elif o1_ye == o2_ys:
            y_rel = 'meets'
        elif o2_ye == o1_ys:
            y_rel = 'meets_i'    
        elif o1_ys == o2_ys and o1_ye < o2_ye:
            y_rel = 'starts'
        elif o1_ys == o2_ys and o1_ye > o2_ye:
            y_rel = 'starts_i'
        elif o1_ye == o2_ye and o1_ys > o2_ys:
            y_rel = 'finishes'
        elif o1_ye == o2_ye and o1_ys < o2_ys:
            y_rel = 'finishes_i'
        elif o1_ye == o2_ye and o1_ys == o2_ys:
            y_rel = 'equal'
        elif o1_ys > o2_ys and o1_ye < o2_ye:
            y_rel = 'during'
        elif o1_ys < o2_ys and o1_ye > o2_ye:
            y_rel = 'during_i'    
        elif o1_ys < o2_ys and o1_ye < o2_ye:
            y_rel = 'overlaps'
        elif o1_ys > o2_ys and o1_ye > o2_ye:
            y_rel = 'overlaps_i'    
            
        return(x_rel, y_rel)    
    
    def requestRedraw(self):
        """Requests a redraw of the drawing panel contents.

        The actual redrawing doesn't happen until the next idle time.
        """
        self._reInitBuffer = True
        #print 'redrawing'

    def onPaint(self, event):
        """
        Called when the window is exposed.
        """
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.BufferedPaintDC(self.drawPanel, self.buffer)


        # On Windows, if that's all we do things look a little rough
        # So in order to make scrolling more polished-looking
        # we iterate over the exposed regions and fill in unknown
        # areas with a fall-back pattern.

        if wx.Platform != '__WXMSW__':
            return

        # First get the update rects and subtract off the part that 
        # self.buffer has correct already
        region = self.drawPanel.GetUpdateRegion()
        panelRect = self.drawPanel.GetClientRect()
        offset = list(self.drawPanel.CalcUnscrolledPosition(0,0))
        offset[0] -= self.saved_offset[0]
        offset[1] -= self.saved_offset[1]
        region.Subtract(-offset[0],- offset[1],panelRect.Width, panelRect.Height)

        # Now iterate over the remaining region rects and fill in with a pattern
        rgn_iter = wx.RegionIterator(region)
        if rgn_iter.HaveRects():
            self.setBackgroundMissingFillStyle(dc)
            offset = self.drawPanel.CalcUnscrolledPosition(0,0)
        while rgn_iter:
            r = rgn_iter.GetRect()
            if r.Size != self.drawPanel.ClientSize:
                dc.DrawRectangleRect(r)
            rgn_iter.Next()

    def setBackgroundMissingFillStyle(self, dc):
        if self.backgroundFillBrush is None:
            # Win95 can only handle a 8x8 stipple bitmaps max
            #stippleBitmap = wx.BitmapFromBits("\xf0"*4 + "\x0f"*4,8,8)
            # ...but who uses Win95?
            stippleBitmap = wx.BitmapFromBits("\x06",2,2)
            stippleBitmap.SetMask(wx.Mask(stippleBitmap))
            bgbrush = wx.Brush(wx.WHITE, wx.STIPPLE_MASK_OPAQUE)
            bgbrush.SetStipple(stippleBitmap)
            self.backgroundFillBrush = bgbrush

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(self.backgroundFillBrush)
        dc.SetTextForeground(wx.LIGHT_GREY)
        dc.SetTextBackground(wx.WHITE)
            

    def onEraseBackground(self, event):
        """
        Overridden to do nothing to prevent flicker
        """
        pass


    def onPanelScroll(self, event):
        """
        Called when the user changes scrolls the drawPanel
        """
        # make a note to ourselves to redraw when we get a chance
        self.requestRedraw()
        event.Skip()
        pass

    def drawContents(self, dc):
        """
        Does the actual drawing of all drawing contents with the specified dc
        """
        # PrepareDC sets the device origin according to current scrolling
        self.drawPanel.PrepareDC(dc)

        gdc = self.wrapDC(dc)

        # First pass draws objects
        ordered_selection = []
        for obj in self.contents[::-1]:
            if obj in self.selection:
                obj.draw(gdc, True)
                ordered_selection.append(obj)
            else:
                obj.draw(gdc, False)

        # First pass draws objects
        if self.curTool is not None:
            self.curTool.draw(gdc)

        # Second pass draws selection handles so they're always on top
        for obj in ordered_selection:
            obj.drawHandles(gdc)


    # ==========================
    # == Menu Command Methods ==
    # ==========================

    def doNew(self, event):
        """ Respond to the "New" menu command.
        """
        global _docList
        newFrame = DrawingFrame(None, -1, "Untitled")
        newFrame.Show(True)
        _docList.append(newFrame)


    def doOpen(self, event):
        """ Respond to the "Open" menu command.
        """
        global _docList

        curDir = os.getcwd()
        fileName = wx.FileSelector("Open File", default_extension="psk",
                                  flags = wx.OPEN | wx.FILE_MUST_EXIST)
        if fileName == "": return
        fileName = os.path.join(os.getcwd(), fileName)
        os.chdir(curDir)

        title = os.path.basename(fileName)

        if (self.fileName == None) and (len(self.contents) == 0):
            # Load contents into current (empty) document.
            self.fileName = fileName
            self.SetTitle(os.path.basename(fileName))
            self.loadContents()
        else:
            # Open a new frame for this document.
            newFrame = DrawingFrame(None, -1, os.path.basename(fileName),
                                    fileName=fileName)
            newFrame.Show(True)
            _docList.append(newFrame)


    def doClose(self, event):
        """ Respond to the "Close" menu command.
        """
        global _docList

        if self.dirty:
            if not self.askIfUserWantsToSave("closing"): return

        _docList.remove(self)
        self.Destroy()


    def doSave(self, event):
        """ Respond to the "Save" menu command.
        """
        if self.fileName != None:
            self.saveContents()


    def doSaveAs(self, event):
        """ Respond to the "Save As" menu command.
        """
        if self.fileName == None:
            default = ""
        else:
            default = self.fileName

        curDir = os.getcwd()
        fileName = wx.FileSelector("Save File As", "Saving",
                                  default_filename=default,
                                  default_extension="psk",
                                  wildcard="*.psk",
                                  flags = wx.SAVE | wx.OVERWRITE_PROMPT)
        if fileName == "": return # User cancelled.
        fileName = os.path.join(os.getcwd(), fileName)
        os.chdir(curDir)

        title = os.path.basename(fileName)
        self.SetTitle(title)

        self.fileName = fileName
        self.saveContents()


    def doRevert(self, event):
        """ Respond to the "Revert" menu command.
        """
        if not self.dirty: return

        if wx.MessageBox("Discard changes made to this document?", "Confirm",
                        style = wx.OK | wx.CANCEL | wx.ICON_QUESTION,
                        parent=self) == wx.CANCEL: return
        self.loadContents()


    def doExit(self, event):
        """ Respond to the "Quit" menu command.
        """
        global _docList, _app
        for doc in _docList:
            if not doc.dirty: continue
            doc.Raise()
            if not doc.askIfUserWantsToSave("quitting"): return
            _docList.remove(doc)
            doc.Destroy()

        _app.ExitMainLoop()


    def doUndo(self, event):
        """ Respond to the "Undo" menu command.
        """
        if not self.undoStack: return 

        state = self._buildStoredState()
        self.redoStack.append(state)
        state = self.undoStack.pop()
        self._restoreStoredState(state)

    def doRedo(self, event):
        """ Respond to the "Redo" menu.
        """
        if not self.redoStack: return

        state = self._buildStoredState()
        self.undoStack.append(state)
        state = self.redoStack.pop()
        self._restoreStoredState(state)

    def doSelectAll(self, event):
        """ Respond to the "Select All" menu command.
        """
        self.selectAll()


    def doDuplicate(self, event):
        """ Respond to the "Duplicate" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                newObj = copy.deepcopy(obj)
                pos = obj.getPosition()
                newObj.setPosition(wx.Point(pos.x + 10, pos.y + 10))
                newObj.name = repr(self.obj_counter)
                self.obj_counter += 1
                objs.append(newObj)

        self.contents = objs + self.contents

        self.selectMany(objs)

    def doGroup(self, event):
        """ Respond to the "Group" menu command.
        """
        self.saveUndoInfo()
        if len(self.group_selection) > 1:
            self.groups[self.group_counter] = []
            print 'Grouping group: ' + repr(self.group_counter)
            for obj in self.group_selection:
                self.groups[self.group_counter].append(obj)
                print 'Grouping obj: ' + repr(obj.getName())
                
            self.group_counter += 1            

    def doUngroup(self, event):
        """ Respond to the "Ungroup" menu command.
        """
        self.saveUndoInfo()
        if len(self.group_selection) > 1:
            for group_num in self.groups:
                if len(self.group_selection) == len(self.groups[group_num]):
                    if len(set(self.group_selection).intersection(set(self.groups[group_num]))) == len(self.groups[group_num]):
                        self.groups.pop(group_num)
                        print 'Ungrouping group: ' + repr(group_num)
                        break
                
    def doOrientRight(self, event):
        """ Respond to the "Orient Right" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                obj.orientation = 'RIGHT'
                self.requestRedraw()                
                break
    
    def doOrientLeft(self, event):
        """ Respond to the "Orient Left" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                obj.orientation = 'LEFT'
                self.requestRedraw()
                break
            
    def doOrientDown(self, event):
        """ Respond to the "Orient Down" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                obj.orientation = 'DOWN'
                self.requestRedraw()
                break
     
    def doOrientUp(self, event):
        """ Respond to the "Orient Up" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                obj.orientation = 'UP'
                self.requestRedraw()
                break
            
    def doOrientNone(self, event):
        """ Respond to the "Orient None" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                obj.orientation = None
                self.requestRedraw()
                break
                        
    def doSetRefObj(self, event):
        """ Respond to the "Set/Unset as Ref Obj" menu command.
        """
        self.saveUndoInfo()

        objs = []
        for obj in self.contents:
            if obj in self.selection:
                if obj.ref_obj == False:
                    obj.ref_obj = True
                else:
                    obj.ref_obj = False
                self.requestRedraw()
                break
            
    def doEditObject(self, event):
        """ Respond to the "Edit..." menu command.
        """
        if len(self.selection) != 1: return

        obj = self.selection[0]
        if not obj.hasPropertyEditor(): 
            assert False, "doEditObject called on non-editable"

        ret = obj.doPropertyEdit(self)
        if ret:
            self.dirty = True
            self.requestRedraw()
            self._adjustMenus()


    def doDelete(self, event):
        """ Respond to the "Delete" menu command.
        """
        self.saveUndoInfo()

        for obj in self.selection:
            self.contents.remove(obj)
            # Remove the corresponding object pairs from core9_rels
            objs = self.core9_rels.keys()
            for key in objs:
                if obj.name == key[0] or obj.name == key[1]:
                    self.core9_rels.pop(key)
            del obj
        self.deselectAll()


    def onChooseTool(self, event):
        """ Respond to tool selection menu and tool palette selections
        """
        print 'chossing tool'
        obj = event.GetEventObject()
        id2name = { id_SELECT: "select",
                    id_RECT: "rect",
                  }
        toolID = event.GetId()
        name = id2name.get( toolID )
        
        if name:
            self.setCurrentTool(name)

    def updChooseTool(self, event):
        """UI update event that keeps tool menu in sync with the PaletteIcons"""
        obj = event.GetEventObject()
        id2name = { id_SELECT: "select",
                    id_RECT: "rect",
                  }
        toolID = event.GetId()
        event.Check( toolID == self.curToolIcon.GetId() )


    def doChooseQuality(self, event):
        """Respond to the render quality menu commands
        """
        if event.GetId() == menu_DC:
            self.wrapDC = lambda dc: dc
        else:
            self.wrapDC = lambda dc: wx.GCDC(dc)
        self._adjustMenus()
        self.requestRedraw()

    def doMoveForward(self, event):
        """ Respond to the "Move Forward" menu command.
        """
        if len(self.selection) != 1: return

        self.saveUndoInfo()

        obj = self.selection[0]
        index = self.contents.index(obj)
        if index == 0: return

        del self.contents[index]
        self.contents.insert(index-1, obj)

        self.requestRedraw()
        self._adjustMenus()


    def doMoveToFront(self, event):
        """ Respond to the "Move to Front" menu command.
        """
        if len(self.selection) != 1: return

        self.saveUndoInfo()

        obj = self.selection[0]
        self.contents.remove(obj)
        self.contents.insert(0, obj)

        self.requestRedraw()
        self._adjustMenus()


    def doMoveBackward(self, event):
        """ Respond to the "Move Backward" menu command.
        """
        if len(self.selection) != 1: return

        self.saveUndoInfo()

        obj = self.selection[0]
        index = self.contents.index(obj)
        if index == len(self.contents) - 1: return

        del self.contents[index]
        self.contents.insert(index+1, obj)

        self.requestRedraw()
        self._adjustMenus()


    def doMoveToBack(self, event):
        """ Respond to the "Move to Back" menu command.
        """
        if len(self.selection) != 1: return

        self.saveUndoInfo()

        obj = self.selection[0]
        self.contents.remove(obj)
        self.contents.append(obj)

        self.requestRedraw()
        self._adjustMenus()


    def doShowAbout(self, event):
        """ Respond to the "About pySketch" menu command.
        """
        dialog = wx.Dialog(self, -1, "About pySketch") # ,
                          #style=wx.DIALOG_MODAL | wx.STAY_ON_TOP)
        dialog.SetBackgroundColour(wx.WHITE)

        panel = wx.Panel(dialog, -1)
        panel.SetBackgroundColour(wx.WHITE)

        panelSizer = wx.BoxSizer(wx.VERTICAL)

        boldFont = wx.Font(panel.GetFont().GetPointSize(),
                          panel.GetFont().GetFamily(),
                          wx.NORMAL, wx.BOLD)

        logo = wx.StaticBitmap(panel, -1, wx.Bitmap("images/logo.bmp",
                                                  wx.BITMAP_TYPE_BMP))

        lab1 = wx.StaticText(panel, -1, "sp_rels_gui")
        lab1.SetFont(wx.Font(36, boldFont.GetFamily(), wx.ITALIC, wx.BOLD))
        lab1.SetSize(lab1.GetBestSize())

        imageSizer = wx.BoxSizer(wx.HORIZONTAL)
        imageSizer.Add(logo, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)
        imageSizer.Add(lab1, 0, wx.ALL | wx.ALIGN_CENTRE_VERTICAL, 5)

        lab2 = wx.StaticText(panel, -1, "A simple object-oriented sp_rels gui program.")
        lab2.SetFont(boldFont)
        lab2.SetSize(lab2.GetBestSize())

        lab3 = wx.StaticText(panel, -1, "sp_rels_gui is completely free " + \
                                       "software; please")
        lab3.SetFont(boldFont)
        lab3.SetSize(lab3.GetBestSize())

        lab4 = wx.StaticText(panel, -1, "feel free to adapt or use this " + \
                                       "in any way you like.")
        lab4.SetFont(boldFont)
        lab4.SetSize(lab4.GetBestSize())

        lab5 = wx.StaticText(panel, -1,
                             "Author: Krishna Dubba " + \
                             "(scksrd@leeds.ac.uk)\n"
                             )

        lab5.SetFont(boldFont)
        lab5.SetSize(lab5.GetBestSize())

        btnOK = wx.Button(panel, wx.ID_OK, "OK")

        panelSizer.Add(imageSizer, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab2, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab3, 0, wx.ALIGN_CENTRE)
        panelSizer.Add(lab4, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(lab5, 0, wx.ALIGN_CENTRE)
        panelSizer.Add((10, 10)) # Spacer.
        panelSizer.Add(btnOK, 0, wx.ALL | wx.ALIGN_CENTRE, 5)

        panel.SetAutoLayout(True)
        panel.SetSizer(panelSizer)
        panelSizer.Fit(panel)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(panel, 0, wx.ALL, 10)

        dialog.SetAutoLayout(True)
        dialog.SetSizer(topSizer)
        topSizer.Fit(dialog)

        dialog.Centre()

        btn = dialog.ShowModal()
        dialog.Destroy()

    def getTextEditor(self):
        if not hasattr(self,'textEditor') or not self.textEditor:
            self.textEditor = EditTextObjectDialog(self, "Edit Text Object")
        return self.textEditor

    # =============================
    # == Object Creation Methods ==
    # =============================

    def addObject(self, obj, select=True):
        """Add a new drawing object to the canvas.
        
        If select is True then also select the object
        """
        self.saveUndoInfo()
        self.contents.insert(0, obj)
        self.dirty = True
        if select:
            self.select(obj)
        #self.setCurrentTool('select')

    def saveUndoInfo(self):
        """ Remember the current state of the document, to allow for undo.^^egnath
        
            We make a copy of the document's contents, so that we can return to
            the previous contents if the user does something and then wants to
            undo the operation.
            
            This should be called only for a new modification to the document
            since it erases the redo history.
        """
        state = self._buildStoredState()

        self.undoStack.append(state)
        self.redoStack = []
        self.dirty = True
        self._adjustMenus()

    # =======================
    # == Selection Methods ==
    # =======================

    def setCurrentTool(self, toolName):
        """ Set the currently selected tool.
        """
        
        toolIcon, tool = self.tools[toolName]
        if self.curToolIcon is not None:
            self.curToolIcon.SetValue(False)

        toolIcon.SetValue(True)
        self.curToolName = toolName
        self.curToolIcon = toolIcon
        self.curTool = tool
        self.drawPanel.SetCursor(tool.getDefaultCursor())


    def selectAll(self):
        """ Select every DrawingObject in our document.
        """
        self.selection = []
        for obj in self.contents:
            self.selection.append(obj)
        self.requestRedraw()
        self._adjustMenus()


    def deselectAll(self):
        """ Deselect every DrawingObject in our document.
        """
        self.selection = []
        self.requestRedraw()
        self._adjustMenus()


    def select(self, obj, add=False):
        """ Select the given DrawingObject within our document.

        If 'add' is True obj is added onto the current selection
        """
        if not add:
            self.selection = []
        if obj not in self.selection:
            self.selection += [obj]
            self.objSize.SetLabel(repr(obj.size.GetWidth()) + ' x ' + repr(obj.size.GetHeight()))
            self.objPos.SetLabel(repr(obj.position.x) + ', ' + repr(obj.position.y))
            self.objName.SetValue(obj.name)
            self.requestRedraw()
            self._adjustMenus()

    def selectMany(self, objs):
        """ Select the given list of DrawingObjects.
        """
        self.selection = objs
        self.requestRedraw()
        self._adjustMenus()


    def selectByRectangle(self, x, y, width, height):
        """ Select every DrawingObject in the given rectangular region.
        """
        self.selection = []
        for obj in self.contents:
            if obj.objectWithinRect(x, y, width, height):
                self.selection.append(obj)
        # This is in case we want to group the selected objects        
        self.group_selection = self.selection
        
        self.requestRedraw()
        self._adjustMenus()        

    def getObjectAndSelectionHandleAt(self, pt):
        """ Return the object and selection handle at the given point.

            We draw selection handles (small rectangles) around the currently
            selected object(s).  If the given point is within one of the
            selection handle rectangles, we return the associated object and a
            code indicating which selection handle the point is in.  If the
            point isn't within any selection handle at all, we return the tuple
            (None, None).
        """
        for obj in self.selection:
            handle = obj.getSelectionHandleContainingPoint(pt.x, pt.y)
            if handle is not None:
                return obj, handle

        return None, None


    def getObjectAt(self, pt):
        """ Return the first object found which is at the given point.
        """
        for obj in self.contents:
            if obj.objectContainsPoint(pt.x, pt.y):
                return obj
        return None


    # ======================
    # == File I/O Methods ==
    # ======================

    def loadContents(self):
        """ Load the contents of our document into memory.
        """
        try:
            f = open(self.fileName, "rb")
            self.frame_data = cPickle.load(f)
            f.close()
        except:
            response = wx.MessageBox("Unable to load " + self.fileName + ".",
                                     "Error", wx.OK|wx.ICON_ERROR, self)
            
        self.edit = False    
        self.slider.SetValue(INITIAL_FRAME)
        
        self.dirty = False
        self.selection = []
        self.undoStack  = []
        self.redoStack  = []

        try:
            state = self.frame_data[self.current_frame]
        except KeyError:
            pass
        self._restoreStoredState(state)
        
        self._adjustMenus()


    def saveContents(self):
        """ Save the contents of our document to disk.
        """
        # SWIG-wrapped native wx contents cannot be pickled, so 
        # we have to convert our data to something pickle-friendly.
        self.frame_data[self.current_frame] = self._buildStoredState()
            
        try:
            f = open(self.fileName, "wb")
            cPickle.dump(self.frame_data, f)
            f.close()
        except:
            response = wx.MessageBox("Unable to load " + self.fileName + ".",
                                     "Error", wx.OK|wx.ICON_ERROR, self)
            
        self.dirty = False
        self._adjustMenus()
            

    def askIfUserWantsToSave(self, action):
        """ Give the user the opportunity to save the current document.

            'action' is a string describing the action about to be taken.  If
            the user wants to save the document, it is saved immediately.  If
            the user cancels, we return False.
        """
        if not self.dirty: return True # Nothing to do.

        response = wx.MessageBox("Save changes before " + action + "?",
                                "Confirm", wx.YES_NO | wx.CANCEL, self)

        if response == wx.YES:
            if self.fileName == None:
                fileName = wx.FileSelector("Save File As", "Saving",
                                          default_extension="psk",
                                          wildcard="*.psk",
                                          flags = wx.SAVE | wx.OVERWRITE_PROMPT)
                if fileName == "": return False # User cancelled.
                self.fileName = fileName

            self.saveContents()
            return True
        elif response == wx.NO:
            return True # User doesn't want changes saved.
        elif response == wx.CANCEL:
            return False # User cancelled.

    # =====================
    # == Private Methods ==
    # =====================

    def _initBuffer(self):
        """Initialize the bitmap used for buffering the display."""
        size = self.drawPanel.GetSize()
        self.buffer = wx.EmptyBitmap(max(1,size.width),max(1,size.height))
        dc = wx.BufferedDC(None, self.buffer)
        dc.SetBackground(wx.Brush(self.drawPanel.GetBackgroundColour()))
        dc.Clear()
        self.drawContents(dc)
        del dc  # commits all drawing to the buffer

        self.saved_offset = self.drawPanel.CalcUnscrolledPosition(0,0)

        self._reInitBuffer = False



    def _adjustMenus(self):
        """ Adjust our menus and toolbar to reflect the current state of the
            world.

            Doing this manually rather than using an EVT_UPDATE_UI is a bit
            more efficient (since it's only done when it's really needed), 
            but it means we have to remember to call _adjustMenus any time
            menus may need adjusting.
        """
        canSave   = (self.fileName != None) and self.dirty
        canRevert = (self.fileName != None) and self.dirty
        canUndo   = self.undoStack!=[]
        canRedo   = self.redoStack!=[]
        selection = len(self.selection) > 0
        onlyOne   = len(self.selection) == 1
        hasEditor = onlyOne and self.selection[0].hasPropertyEditor()
        front     = onlyOne and (self.selection[0] == self.contents[0])
        back      = onlyOne and (self.selection[0] == self.contents[-1])

        # Enable/disable our menu items.

        self.fileMenu.Enable(wx.ID_SAVE,   canSave)
        self.fileMenu.Enable(wx.ID_REVERT, canRevert)

        self.editMenu.Enable(wx.ID_UNDO,      canUndo)
        self.editMenu.Enable(wx.ID_REDO,      canRedo)
        self.editMenu.Enable(menu_DUPLICATE, selection)
        self.editMenu.Enable(menu_EDIT_PROPS,hasEditor)
        self.editMenu.Enable(wx.ID_CLEAR,    selection)

        self.objectMenu.Enable(menu_MOVE_FORWARD,  onlyOne and not front)
        self.objectMenu.Enable(menu_MOVE_TO_FRONT, onlyOne and not front)
        self.objectMenu.Enable(menu_MOVE_BACKWARD, onlyOne and not back)
        self.objectMenu.Enable(menu_MOVE_TO_BACK,  onlyOne and not back)

        # Enable/disable our toolbar icons.

        self.toolbar.EnableTool(wx.ID_NEW,          True)
        self.toolbar.EnableTool(wx.ID_OPEN,         True)
        self.toolbar.EnableTool(wx.ID_SAVE,         canSave)
        self.toolbar.EnableTool(wx.ID_UNDO,         canUndo)
        self.toolbar.EnableTool(wx.ID_REDO,         canRedo)
        self.toolbar.EnableTool(menu_DUPLICATE,     selection)
        self.toolbar.EnableTool(menu_MOVE_FORWARD,  onlyOne and not front)
        self.toolbar.EnableTool(menu_MOVE_BACKWARD, onlyOne and not back)


    def _setPenColour(self, colour):
        """ Set the default or selected object's pen colour.
        """
        if len(self.selection) > 0:
            self.saveUndoInfo()
            for obj in self.selection:
                obj.setPenColour(colour)
            self.requestRedraw()

        self.penColour = colour
        self.optionIndicator.setPenColour(colour)


    def _setFillColour(self, colour):
        """ Set the default or selected object's fill colour.
        """
        if len(self.selection) > 0:
            self.saveUndoInfo()
            for obj in self.selection:
                obj.setFillColour(colour)
            self.requestRedraw()

        self.fillColour = colour
        self.optionIndicator.setFillColour(colour)


    def _setLineSize(self, size):
        """ Set the default or selected object's line size.
        """
        if len(self.selection) > 0:
            self.saveUndoInfo()
            for obj in self.selection:
                obj.setLineSize(size)
            self.requestRedraw()

        self.lineSize = size
        self.optionIndicator.setLineSize(size)

    def _setObjType(self, objType):
        """ Set the default or selected object's type.
        """
        if len(self.selection) > 0:
            self.saveUndoInfo()
            for obj in self.selection:
                obj.setObjType(objType)
            self.requestRedraw()

        self.optionIndicator.setObjType(objType)

    def _buildStoredState(self):
        """ Remember the current state of the document, to allow for undo.

            We make a copy of the document's contents, so that we can return to
            the previous contents if the user does something and then wants to
            undo the operation.  

            Returns an object representing the current document state.
        """
        savedContents = []
        for obj in self.contents:
            savedContents.append([obj.__class__, obj.getData()])

        savedSelection = []
        for i in range(len(self.contents)):
            if self.contents[i] in self.selection:
                savedSelection.append(i)

        info = {"contents"  : savedContents,
                "selection" : savedSelection,
                "groups"    : self.groups}
        
        return info
        
    def _restoreStoredState(self, savedState):
        """Restore the state of the document to a previous point for undo/redo.

        Takes a stored state object and recreates the document from it.
        Used by undo/redo implementation.
        """
        self.contents = []

        for draw_class, obj_data in savedState["contents"]:
            obj_name = obj_data[-1]                
            # Get initial values, these are temporary
            (name, position, size, penColour, fillColour, lineSize) = (obj_name, wx.Point(0, 0), \
                                                                       wx.Size(0, 0), wx.BLACK, wx.WHITE, 1)
            obj = draw_class(name, position, size, penColour, fillColour, lineSize)
            # Now set the real values 
            obj.setData(obj_data)
            self.contents.append(obj)
           
        self.selection = []
        for i in savedState["selection"]:
            self.selection.append(self.contents[i])
        
        self.groups = savedState['groups']

        self.dirty = True
        self._adjustMenus()
        self.requestRedraw()

    def _resizeObject(self, obj, anchorPt, oldPt, newPt):
        """ Resize the given object.

            'anchorPt' is the unchanging corner of the object, while the
            opposite corner has been resized.  'oldPt' are the current
            coordinates for this corner, while 'newPt' are the new coordinates.
            The object should fit within the given dimensions, though if the
            new point is less than the anchor point the object will need to be
            moved as well as resized, to avoid giving it a negative size.
        """
        if isinstance(obj, TextDrawingObject):
            # Not allowed to resize text objects -- they're sized to fit text.
            wx.Bell()
            return

        self.saveUndoInfo()

        topLeft  = wx.Point(min(anchorPt.x, newPt.x),
                           min(anchorPt.y, newPt.y))
        botRight = wx.Point(max(anchorPt.x, newPt.x),
                           max(anchorPt.y, newPt.y))

        newWidth  = botRight.x - topLeft.x
        newHeight = botRight.y - topLeft.y

        if isinstance(obj, LineDrawingObject):
            # Adjust the line so that its start and end points match the new
            # overall object size.

            startPt = obj.getStartPt()
            endPt   = obj.getEndPt()

            slopesDown = ((startPt.x < endPt.x) and (startPt.y < endPt.y)) or \
                         ((startPt.x > endPt.x) and (startPt.y > endPt.y))

            # Handle the user flipping the line.

            hFlip = ((anchorPt.x < oldPt.x) and (anchorPt.x > newPt.x)) or \
                    ((anchorPt.x > oldPt.x) and (anchorPt.x < newPt.x))
            vFlip = ((anchorPt.y < oldPt.y) and (anchorPt.y > newPt.y)) or \
                    ((anchorPt.y > oldPt.y) and (anchorPt.y < newPt.y))

            if (hFlip and not vFlip) or (vFlip and not hFlip):
                slopesDown = not slopesDown # Line flipped.

            if slopesDown:
                obj.setStartPt(wx.Point(0, 0))
                obj.setEndPt(wx.Point(newWidth, newHeight))
            else:
                obj.setStartPt(wx.Point(0, newHeight))
                obj.setEndPt(wx.Point(newWidth, 0))

        # Finally, adjust the bounds of the object to match the new dimensions.

        obj.setPosition(topLeft)
        obj.setSize(wx.Size(botRight.x - topLeft.x, botRight.y - topLeft.y))
        print 'resized'
        self.requestRedraw()
        

    def _moveObject(self, offsetX, offsetY):
        """ Move the currently selected object(s) by the given offset using arrow keys.
        """
        self.saveUndoInfo()

        # Use this only to move group of objects
        #for obj in self.selection:
        for obj in self.group_selection:
            pos = obj.getPosition()
            pos.x = pos.x + offsetX
            pos.y = pos.y + offsetY
            obj.setPosition(pos)

        self.requestRedraw()


    def _buildLineSizePopup(self, lineSize):
        """ Build the pop-up menu used to set the line size.

            'lineSize' is the current line size value.  The corresponding item
            is checked in the pop-up menu.
        """
        menu = wx.Menu()
        menu.Append(id_LINESIZE_0, "no line",      kind=wx.ITEM_CHECK)
        menu.Append(id_LINESIZE_1, "1-pixel line", kind=wx.ITEM_CHECK)
        menu.Append(id_LINESIZE_2, "2-pixel line", kind=wx.ITEM_CHECK)
        menu.Append(id_LINESIZE_3, "3-pixel line", kind=wx.ITEM_CHECK)
        menu.Append(id_LINESIZE_4, "4-pixel line", kind=wx.ITEM_CHECK)
        menu.Append(id_LINESIZE_5, "5-pixel line", kind=wx.ITEM_CHECK)

        if   lineSize == 0: menu.Check(id_LINESIZE_0, True)
        elif lineSize == 1: menu.Check(id_LINESIZE_1, True)
        elif lineSize == 2: menu.Check(id_LINESIZE_2, True)
        elif lineSize == 3: menu.Check(id_LINESIZE_3, True)
        elif lineSize == 4: menu.Check(id_LINESIZE_4, True)
        elif lineSize == 5: menu.Check(id_LINESIZE_5, True)

        self.Bind(wx.EVT_MENU, self._lineSizePopupSelected, id=id_LINESIZE_0, id2=id_LINESIZE_5)

        return menu

    def _lineSizePopupSelected(self, event):
        """ Respond to the user selecting an item from the line size popup menu
        """
        id = event.GetId()
        if   id == id_LINESIZE_0: self._setLineSize(0)
        elif id == id_LINESIZE_1: self._setLineSize(1)
        elif id == id_LINESIZE_2: self._setLineSize(2)
        elif id == id_LINESIZE_3: self._setLineSize(3)
        elif id == id_LINESIZE_4: self._setLineSize(4)
        elif id == id_LINESIZE_5: self._setLineSize(5)
        else:
            wx.Bell()
            return

        self.optionIndicator.setLineSize(self.lineSize)

    def _buildObjTypePopup(self, objType):
        """ Build the pop-up menu used to set the object type.
            'lineSize' is the current line size value.  The corresponding item
            is checked in the pop-up menu.
        """
        menu = wx.Menu()
        menu.Append(id_OBJTYPE_0, "robot",      kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_1, "guest",      kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_2, "counter",    kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_3, "table",      kind=wx.ITEM_CHECK)        
        menu.Append(id_OBJTYPE_4, "chair",      kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_5, "mug",        kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_6, "spoon",      kind=wx.ITEM_CHECK)
        menu.Append(id_OBJTYPE_7, "region",     kind=wx.ITEM_CHECK)
        
        if   objType == 0: menu.Check(id_OBJTYPE_0, True)
        elif objType == 1: menu.Check(id_OBJTYPE_1, True)
        elif objType == 2: menu.Check(id_OBJTYPE_2, True)
        elif objType == 3: menu.Check(id_OBJTYPE_3, True)
        elif objType == 4: menu.Check(id_OBJTYPE_4, True)
        elif objType == 5: menu.Check(id_OBJTYPE_5, True)
        elif objType == 6: menu.Check(id_OBJTYPE_6, True)
        elif objType == 7: menu.Check(id_OBJTYPE_7, True)

        self.Bind(wx.EVT_MENU, self._objTypePopupSelected, id=id_OBJTYPE_0, id2=id_OBJTYPE_7)

        return menu


    def _objTypePopupSelected(self, event):
        """ Respond to the user selecting an item from the line size popup menu
        """
        id = event.GetId()
        if   id == id_OBJTYPE_0: self._setObjType("robot")
        elif id == id_OBJTYPE_1: self._setObjType("guest")
        elif id == id_OBJTYPE_2: self._setObjType("counter")
        elif id == id_OBJTYPE_3: self._setObjType("table")
        elif id == id_OBJTYPE_4: self._setObjType("chair")
        elif id == id_OBJTYPE_5: self._setObjType("mug")
        elif id == id_OBJTYPE_6: self._setObjType("spoon")
        elif id == id_OBJTYPE_7: self._setObjType("region")
        else:
            wx.Bell()
            return

        self.optionIndicator.setObjType(None)


    def _getEventCoordinates(self, event):
        """ Return the coordinates associated with the given mouse event.

            The coordinates have to be adjusted to allow for the current scroll
            position.
        """
        originX, originY = self.drawPanel.GetViewStart()
        unitX, unitY = self.drawPanel.GetScrollPixelsPerUnit()
        return wx.Point(event.GetX() + (originX * unitX),
                       event.GetY() + (originY * unitY))


    def _drawObjectOutline(self, offsetX, offsetY):
        """ Draw an outline of the currently selected object.

            The selected object's outline is drawn at the object's position
            plus the given offset.

            Note that the outline is drawn by *inverting* the window's
            contents, so calling _drawObjectOutline twice in succession will
            restore the window's contents back to what they were previously.
        """
        if len(self.selection) != 1: return

        position = self.selection[0].getPosition()
        size     = self.selection[0].getSize()

        dc = wx.ClientDC(self.drawPanel)
        self.drawPanel.PrepareDC(dc)
        dc.BeginDrawing()
        dc.SetPen(wx.BLACK_DASHED_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.SetLogicalFunction(wx.INVERT)

        dc.DrawRectangle(position.x + offsetX, position.y + offsetY,
                         size.width, size.height)

        dc.EndDrawing()


#============================================================================
class DrawingTool(object):
    """Base class for drawing tools"""

    def __init__(self):
        pass

    def getDefaultCursor(self):
        """Return the cursor to use by default which this drawing tool is selected"""
        return wx.STANDARD_CURSOR

    def draw(self,dc):
        pass


    def onMouseEvent(self,parent, event):
        """Mouse events passed in from the parent.

        Returns True if the event is handled by the tool,
        False if the canvas can try to use it.
        """
        event.Skip()
        return False

#----------------------------------------------------------------------------
class SelectDrawingTool(DrawingTool):
    """Represents the tool for selecting things"""

    def __init__(self):
        self.curHandle = None
        self.curObject = None
        self.objModified = False
        self.startPt = None
        self.curPt = None

    def getDefaultCursor(self):
        """Return the cursor to use by default which this drawing tool is selected"""
        return wx.STANDARD_CURSOR

    def draw(self, dc):
        if self._doingRectSelection():
            dc.SetPen(wx.BLACK_DASHED_PEN)
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            x = [self.startPt.x, self.curPt.x]; x.sort()
            y = [self.startPt.y, self.curPt.y]; y.sort()
            dc.DrawRectangle(x[0],y[0], x[1]-x[0],y[1]-y[0])


    def onMouseEvent(self,parent, event):
        handlers = { wx.EVT_LEFT_DOWN.evtType[0]:   self.onMouseLeftDown,
                     wx.EVT_MOTION.evtType[0]:      self.onMouseMotion,
                     wx.EVT_LEFT_UP.evtType[0]:     self.onMouseLeftUp,
                     wx.EVT_LEFT_DCLICK.evtType[0]: self.onMouseLeftDClick }
        handler = handlers.get(event.GetEventType())
        if handler is not None:
            return handler(parent,event)
        else:
            event.Skip()
            return False

    def onMouseLeftDown(self,parent,event):
        mousePt = wx.Point(event.X,event.Y)
        obj, handle = parent.getObjectAndSelectionHandleAt(mousePt)
        self.startPt = mousePt
        self.curPt = mousePt
        if obj is not None and handle is not None:
            self.curObject = obj
            self.curHandle = handle
        else:
            self.curObject = None
            self.curHandle = None
        
        obj = parent.getObjectAt(mousePt)
        if self.curObject is None and obj is not None:
            self.curObject = obj
            self.dragDelta = obj.position-mousePt
            self.curHandle = None
            parent.select(obj, event.ShiftDown())
            
        return True

    def onMouseMotion(self,parent,event):
        if not event.LeftIsDown(): return

        self.curPt = wx.Point(event.X,event.Y)

        obj,handle = self.curObject,self.curHandle
        if self._doingDragHandle():
            self._prepareToModify(parent)
            obj.moveHandle(handle,event.X,event.Y)
            #parent.requestRedraw()

        elif self._doingDragObject():
            self._prepareToModify(parent)
            obj.position = self.curPt + self.dragDelta
            #parent.requestRedraw()

        #elif self._doingRectSelection():
        #    parent.requestRedraw()
        
        if self.curObject != None:
            parent.objSize.SetLabel(repr(self.curObject.size.GetWidth()) + ' x ' + repr(self.curObject.size.GetHeight()))
        parent.requestRedraw()
        return True

    def onMouseLeftUp(self,parent,event):

        obj,handle = self.curObject,self.curHandle
        if self._doingDragHandle():
            obj.moveHandle(handle,event.X,event.Y)
            obj.finalizeHandle(handle,event.X,event.Y)

        elif self._doingDragObject():
            curPt = wx.Point(event.X,event.Y)
            obj.position = curPt + self.dragDelta

        elif self._doingRectSelection():
            x = [event.X, self.startPt.x]
            y = [event.Y, self.startPt.y]
            x.sort()
            y.sort()
            parent.selectByRectangle(x[0],y[0],x[1]-x[0],y[1]-y[0])
            

        self.curObject = None
        self.curHandle = None
        self.curPt = None
        self.startPt = None
        self.objModified = False
        parent.requestRedraw()

        return True

    def onMouseLeftDClick(self,parent,event):
        event.Skip()
        mousePt = wx.Point(event.X,event.Y)
        obj = parent.getObjectAt(mousePt)
        if obj and obj.hasPropertyEditor():
            if obj.doPropertyEdit(parent):
                parent.requestRedraw()
                return True

        return False
    
    def _prepareToModify(self,parent):
        if not self.objModified:
            parent.saveUndoInfo()
            self.objModified = True
        
    def _doingRectSelection(self):
        return self.curObject is None \
               and self.startPt is not None \
               and self.curPt is not None

    def _doingDragObject(self):
        return self.curObject is not None and self.curHandle is None

    def _doingDragHandle(self):
        return self.curObject is not None and self.curHandle is not None


#----------------------------------------------------------------------------
class RectDrawingTool(DrawingTool):
    """Represents the tool for drawing rectangles"""

    def __init__(self):
        self.newObject = None

    def getDefaultCursor(self):
        """Return the cursor to use by default which this drawing tool is selected"""
        return wx.CROSS_CURSOR

    def draw(self, dc):
        if self.newObject is None: return
        self.newObject.draw(dc,True)


    def onMouseEvent(self,parent, event):
        handlers = { wx.EVT_LEFT_DOWN.evtType[0]: self.onMouseLeftDown,
                     wx.EVT_MOTION.evtType[0]:    self.onMouseMotion,
                     wx.EVT_LEFT_UP.evtType[0]:   self.onMouseLeftUp }
        handler = handlers.get(event.GetEventType())
        if handler is not None:
            return handler(parent,event)
        else:
            event.Skip()
            return False

    def onMouseLeftDown(self,parent, event):
        self.startPt = wx.Point(event.GetX(), event.GetY())
        self.newObject = None
        event.Skip()
        return True

    def onMouseMotion(self,parent, event):
        if not event.Dragging(): return

        if self.newObject is None:
            obj = RectDrawingObject(penColour=parent.penColour,
                                    fillColour=parent.fillColour,
                                    lineSize=parent.lineSize, 
                                    name=parent.obj_counter)
            parent.obj_counter += 1
            self.newObject = obj

        self._updateObjFromEvent(self.newObject, event)
        parent.objSize.SetLabel(repr(self.newObject.size.GetWidth()) + ' x ' + repr(self.newObject.size.GetHeight()))        
        parent.objPos.SetLabel(repr(self.newObject.position.x) + ', ' + repr(self.newObject.position.y))
        parent.requestRedraw()
        event.Skip()
        return True

    def onMouseLeftUp(self,parent, event):

        if self.newObject is None:
            return

        self._updateObjFromEvent(self.newObject,event)

        parent.addObject(self.newObject)

        self.newObject = None

        event.Skip()
        return True


    def _updateObjFromEvent(self,obj,event):
        x = [event.X, self.startPt.x]
        y = [event.Y, self.startPt.y]
        x.sort()
        y.sort()
        width = x[1]-x[0]
        height = y[1]-y[0]

        obj.setPosition(wx.Point(x[0],y[0]))
        obj.setSize(wx.Size(width,height))

#============================================================================
class DrawingObject(object):
    """ Base class for objects within the drawing panel.

        A pySketch document consists of a front-to-back ordered list of
        DrawingObjects.  Each DrawingObject has the following properties:

            'position'      The position of the object within the document.
            'size'          The size of the object within the document.
            'penColour'     The colour to use for drawing the object's outline.
            'fillColour'    Colour to use for drawing object's interior.
            'lineSize'      Line width (in pixels) to use for object's outline.
            """

    # ==================
    # == Constructors ==
    # ==================

    def __init__(self, name, position=wx.Point(0, 0), size=wx.Size(0, 0),
                 penColour=wx.BLACK, fillColour=wx.WHITE, lineSize=1, objType='obj'
                 ):
        """ Standard constructor.

            The remaining parameters let you set various options for the newly
            created DrawingObject.
        """
        # One must take great care with constructed default arguments
        # like wx.Point(0,0) above.  *EVERY* caller that uses the
        # default will get the same instance.  Thus, below we make a
        # deep copy of those arguments with object defaults.

        self.position          = wx.Point(position.x,position.y)
        self.size              = wx.Size(size.x,size.y)
        self.penColour         = penColour
        self.fillColour        = fillColour
        self.lineSize          = lineSize
        self.objType           = objType
        self.name              = repr(name)        

    # =============================
    # == Object Property Methods ==
    # =============================

    def getData(self):
        """ Return a copy of the object's internal data.

            This is used to save this DrawingObject to disk.
        """
        return [self.position.x, self.position.y,
                self.size.width, self.size.height,
                self.orientation,
                self.penColour.Red(),
                self.penColour.Green(),
                self.penColour.Blue(),
                self.fillColour.Red(),
                self.fillColour.Green(),
                self.fillColour.Blue(),
                self.lineSize,
                self.ref_obj,
                self.objType,
                self.name]

    def setData(self, data):
        """ Set the object's internal data.

            'data' is a copy of the object's saved data, as returned by
            getData() above.  This is used to restore a previously saved
            DrawingObject.

            Returns an iterator to any remaining data not consumed by 
            this base class method.
        """
        #data = copy.deepcopy(data) # Needed?

        d = iter(data)
        try:
            self.position          = wx.Point(d.next(), d.next())
            self.size              = wx.Size(d.next(), d.next())
            self.orientation       = d.next()
            self.penColour         = wx.Colour(red=d.next(),
                                              green=d.next(),
                                              blue=d.next())
            self.fillColour        = wx.Colour(red=d.next(),
                                              green=d.next(),
                                              blue=d.next())
            self.lineSize          = d.next()
            self.ref_obj           = d.next()
            self.objType           = d.next()
            self.name              = d.next()
        except StopIteration:
            raise ValueError('Not enough data in setData call')

        return d


    def hasPropertyEditor(self):
        #return False
        return True

    def doPropertyEdit(self, parent):
        #assert False, "Must be overridden if hasPropertyEditor returns True"
        assert True, "Must be overridden if hasPropertyEditor returns True"

    def setPosition(self, position):
        """ Set the origin (top-left corner) for this DrawingObject.
        """
        self.position = position


    def getPosition(self):
        """ Return this DrawingObject's position.
        """
        return self.position


    def setSize(self, size):
        """ Set the size for this DrawingObject.
        """
        self.size = size

    def getSize(self):
        """ Return this DrawingObject's size.
        """
        return self.size

    def setObjType(self, objType):
        """ Set the obj type for this DrawingObject.
        """
        self.objType = objType

    def getObjType(self):
        """ Get the obj type for this DrawingObject.
        """
        return self.objType

    def getName(self):
        """ Return this DrawingObject's name.
        """
        return self.name

    def setName(self, name):
        """ Set this DrawingObject's name.
        """
        self.name = name
        
    def setPenColour(self, colour):
        """ Set the pen colour used for this DrawingObject.
        """
        self.penColour = colour


    def getPenColour(self):
        """ Return this DrawingObject's pen colour.
        """
        return self.penColour


    def setFillColour(self, colour):
        """ Set the fill colour used for this DrawingObject.
        """
        self.fillColour = colour


    def getFillColour(self):
        """ Return this DrawingObject's fill colour.
        """
        return self.fillColour


    def setLineSize(self, lineSize):
        """ Set the linesize used for this DrawingObject.
        """
        self.lineSize = lineSize


    def getLineSize(self):
        """ Return this DrawingObject's line size.
        """
        return self.lineSize


    # ============================
    # == Object Drawing Methods ==
    # ============================

    def draw(self, dc, selected):
        """ Draw this DrawingObject into our window.

            'dc' is the device context to use for drawing.  

            If 'selected' is True, the object is currently selected.
            Drawing objects can use this to change the way selected objects
            are drawn, however the actual drawing of selection handles
            should be done in the 'drawHandles' method
        """
        if self.lineSize == 0:
            dc.SetPen(wx.Pen(self.penColour, self.lineSize, wx.TRANSPARENT))
        else:
            dc.SetPen(wx.Pen(self.penColour, self.lineSize, wx.SOLID))
        dc.SetBrush(wx.Brush(self.fillColour, wx.SOLID))

        self._privateDraw(dc, self.position, selected)


    def drawHandles(self, dc):
        """Draw selection handles for this DrawingObject"""

        # Default is to draw selection handles at all four corners.
        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.BLACK_BRUSH)
        
        x,y = self.position
        self._drawSelHandle(dc, x, y)
        self._drawSelHandle(dc, x + self.size.width, y)
        self._drawSelHandle(dc, x, y + self.size.height)
        self._drawSelHandle(dc, x + self.size.width, y + self.size.height)


    # =======================
    # == Selection Methods ==
    # =======================

    def objectContainsPoint(self, x, y):
        """ Returns True iff this object contains the given point.

            This is used to determine if the user clicked on the object.
        """
        # Firstly, ignore any points outside of the object's bounds.

        if x < self.position.x: return False
        if x > self.position.x + self.size.x: return False
        if y < self.position.y: return False
        if y > self.position.y + self.size.y: return False

        # Now things get tricky.  There's no straightforward way of
        # knowing whether the point is within an arbitrary object's
        # bounds...to get around this, we draw the object into a
        # memory-based bitmap and see if the given point was drawn.
        # This could no doubt be done more efficiently by some tricky
        # maths, but this approach works and is simple enough.

        # Subclasses can implement smarter faster versions of this.

        bitmap = wx.EmptyBitmap(self.size.x + 10, self.size.y + 10)
        dc = wx.MemoryDC()
        dc.SelectObject(bitmap)
        dc.BeginDrawing()
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        dc.SetPen(wx.Pen(wx.BLACK, self.lineSize + 5, wx.SOLID))
        dc.SetBrush(wx.BLACK_BRUSH)
        self._privateDraw(dc, wx.Point(5, 5), True)
        dc.EndDrawing()
        pixel = dc.GetPixel(x - self.position.x + 5, y - self.position.y + 5)
        if (pixel.Red() == 0) and (pixel.Green() == 0) and (pixel.Blue() == 0):
            return True
        else:
            return False

    handle_TOP    = 0
    handle_BOTTOM = 1
    handle_LEFT   = 0
    handle_RIGHT  = 1

    def getSelectionHandleContainingPoint(self, x, y):
        """ Return the selection handle containing the given point, if any.

            We return one of the predefined selection handle ID codes.
        """
        # Default implementation assumes selection handles at all four bbox corners.
        # Return a list so we can modify the contents later in moveHandle()
        if self._pointInSelRect(x, y, self.position.x, self.position.y):
            return [self.handle_TOP, self.handle_LEFT]
        elif self._pointInSelRect(x, y, self.position.x + self.size.width,
                                        self.position.y):
            return [self.handle_TOP, self.handle_RIGHT]
        elif self._pointInSelRect(x, y, self.position.x,
                                        self.position.y + self.size.height):
            return [self.handle_BOTTOM, self.handle_LEFT]
        elif self._pointInSelRect(x, y, self.position.x + self.size.width,
                                        self.position.y + self.size.height):
            return [self.handle_BOTTOM, self.handle_RIGHT]
        else:
            return None

    def moveHandle(self, handle, x, y):
        """ Move the specified selection handle to given canvas location.
        """
        assert handle is not None

        # Default implementation assumes selection handles at all four bbox corners.
        pt = wx.Point(x,y)
        x,y = self.position
        w,h = self.size
        if handle[0] == self.handle_TOP:
            if handle[1] == self.handle_LEFT:
                dpos = pt - self.position
                self.position = pt
                self.size.width -= dpos.x
                self.size.height -= dpos.y
            else:
                dx = pt.x - ( x + w )
                dy = pt.y - ( y )
                self.position.y = pt.y
                self.size.width += dx
                self.size.height -= dy
        else: # BOTTOM
            if handle[1] == self.handle_LEFT:
                dx = pt.x - ( x )
                dy = pt.y - ( y + h )
                self.position.x = pt.x
                self.size.width -= dx
                self.size.height += dy
            else: 
                dpos = pt - self.position
                dpos.x -= w
                dpos.y -= h
                self.size.width += dpos.x
                self.size.height += dpos.y

        # Finally, normalize so no negative widths or heights.
        # And update the handle variable accordingly.
        if self.size.height<0:
            self.position.y += self.size.height
            self.size.height = -self.size.height
            handle[0] = 1-handle[0]

        if self.size.width<0:
            self.position.x += self.size.width
            self.size.width = -self.size.width
            handle[1] = 1-handle[1]
            

    def finalizeHandle(self, handle, x, y):
        pass

    def objectWithinRect(self, x, y, width, height):
        """ Return True iff this object falls completely within the given rect.
        """
        if x          > self.position.x:                    return False
        if x + width  < self.position.x + self.size.width:  return False
        if y          > self.position.y:                    return False
        if y + height < self.position.y + self.size.height: return False
        return True

    # =====================
    # == Private Methods ==
    # =====================

    def _privateDraw(self, dc, position, selected):
        """ Private routine to draw this DrawingObject.

            'dc' is the device context to use for drawing, while 'position' is
            the position in which to draw the object.
        """
        pass

    def _drawSelHandle(self, dc, x, y):
        """ Draw a selection handle around this DrawingObject.

            'dc' is the device context to draw the selection handle within,
            while 'x' and 'y' are the coordinates to use for the centre of the
            selection handle.
        """
        dc.DrawRectangle(x - 3, y - 3, 6, 6)


    def _pointInSelRect(self, x, y, rX, rY):
        """ Return True iff (x, y) is within the selection handle at (rX, ry).
        """
        if   x < rX - 3: return False
        elif x > rX + 3: return False
        elif y < rY - 3: return False
        elif y > rY + 3: return False
        else:            return True


#----------------------------------------------------------------------------
class RectDrawingObject(DrawingObject):
    """ DrawingObject subclass that represents an axis-aligned rectangle.
    """
    def __init__(self, *varg, **kwarg):
        DrawingObject.__init__(self, *varg, **kwarg)
        self.orientation = 'DOWN'
        self.ref_obj     = False
        
    def objectContainsPoint(self, x, y):
        """ Returns True iff this object contains the given point.

            This is used to determine if the user clicked on the object.
        """
        # Firstly, ignore any points outside of the object's bounds.

        if x < self.position.x: return False
        if x > self.position.x + self.size.x: return False
        if y < self.position.y: return False
        if y > self.position.y + self.size.y: return False

        # Rectangles are easy -- they're always selected if the
        # point is within their bounds.
        return True
       
    # =====================
    # == Private Methods ==
    # =====================

    def draw_contour_lines(self, dc, position, orientation='RIGHT'):
        if self.ref_obj:
          
            if self.orientation == 'UP' or self.orientation == 'DOWN':
                fig_w = self.size.width
                fig_h = self.size.width
                x_left_lim  = self.position.x
                x_right_lim = self.position.x + self.size.width
                if self.orientation == 'UP':
                    y_left_lim  = self.position.y
                    y_right_lim = self.position.y + fig_h
                    x1, y1 = self.position.x, self.position.y
                    x2, y2 = self.position.x + self.size.width, self.position.y
                if self.orientation == 'DOWN':
                    x1, y1 = self.position.x, self.position.y + self.size.height
                    x2, y2 = self.position.x + self.size.width, self.position.y + self.size.height                   
                    y_left_lim  = self.position.y + self.size.height
                    y_right_lim = self.position.y + self.size.height + fig_h
            if self.orientation == 'LEFT' or self.orientation == 'RIGHT':
                fig_w = self.size.height
                fig_h = self.size.height
                y_left_lim  = self.position.y
                y_right_lim = self.position.y + fig_h
                if self.orientation == 'LEFT':
                    x_left_lim  = self.position.x
                    x_right_lim = self.position.x + fig_h
                    x1, y1 = self.position.x, self.position.y
                    x2, y2 = self.position.x, self.position.y + self.size.height                            
                if self.orientation == 'RIGHT':
                    x_left_lim  = self.position.x + self.size.width
                    x_right_lim = self.position.x + self.size.width + fig_w
                    x1, y1 = self.position.x + self.size.width, self.position.y
                    x2, y2 = self.position.x + self.size.width, self.position.y + self.size.height                            
                
            fig = Figure(figsize=(fig_w,fig_h), dpi=120,frameon=False)
            plot = fig.add_subplot(111)
        
            A = 0
            K = 1
            B = 2
            Q = 0.01
            M = 0.01
            
            #x1, y1 = self.position.x, self.position.y
            #x2, y2 = self.position.x, self.position.y
            
            #x_left_lim  = 0
            #x_right_lim = 11
            #y_left_lim  = 0
            #y_right_lim = 4

            x = linspace(x_left_lim, x_right_lim, x_right_lim - x_left_lim)
            y = linspace(y_left_lim, y_right_lim, y_right_lim - y_left_lim)
            X, Y = meshgrid(x, y)
            Z = np.zeros((X.shape[0],X.shape[1]))
            
            for i in range(y.shape[0]):
                for j in range(x.shape[0]):
                    ang = find_angle(x1,y1,x2,y2,x[j],y[i])
                    dist1 = distance(x1, y1, x[j], y[i])
                    dist2 = distance(x2, y2, x[j], y[i])
                    avg_dist = (dist1+dist2)/2
                    if avg_dist == 0:
                        avg_dist = 0.0000001
                    Z[i,j] = 2*gen_logistic(A, K, B, Q, M, ang) + 1/avg_dist

            contour = plot.contour(X, Y, Z)
            for collection in contour.collections:
                for path in collection.get_paths():
                    points_list = []
                    for point in path.vertices:
                        #dc.DrawPoint(point[0], point[1])
                        points_list.append(wx.RealPoint(point[0], point[1]))
                    #dc.DrawSpline(points_list)
                    
    def old_draw_contour(self, dc, position, orientation='RIGHT'):
        """
        Can I use this function in the future?
        DrawSpline(self, points)

          Draws a spline between all given control points, (a list of wx.Point objects) using the current pen. 
          The spline is drawn using a series of lines, using an algorithm taken from the X drawing program 'XFIG'.

          Parameters:
            points 
                  (type=List)
                  
        TODO:
            implement orientation!
        """

        if self.ref_obj:
            #delta = 0.025
            #x = np.arange(-3.0, 3.0, delta)
            #y = np.arange(-2.0, 2.0, delta)
            #X, Y = np.meshgrid(x, y)
            #Z = mlab.bivariate_normal(X, Y, 1.0, 1.0, 0.0, 0.0)
            #matplotlib.rc('figure.subplot', left=.01, right=.01, bottom=.01, top=.01)
            targets = dict(left=0, right=0, top=0, bottom=0, hspace=30, wspace=30)
            
            fig_w = self.size.width/96.0
            fig_h = self.size.width/100.0            
            fig = Figure(figsize=(fig_w,fig_h), dpi=120,frameon=False)
            plot = fig.add_subplot(111)
            adjust_borders(fig, targets)

            canvas = FigureCanvasAgg(fig)
            
            xlist = linspace(-3.0, 3.0, 4)
            ylist = linspace(-3.0, 0, 3)
            X, Y = meshgrid(xlist, ylist)
            Z = sqrt(X**2 + Y**2)
            
            levels = [0.0, 0.5, 1, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]    
            #CP3 = plot.contour(X, Y, Z, levels, colors='k')
            #plot.clabel(CP3, colors = 'k', fmt = '%2.1f', fontsize=14)
            contour = plot.contour(X, Y, Z, levels,alpha=0.8)
            splines = []
            for collection in contour.collections:
                for path in collection.get_paths():
                    points_list = []
                    for point in path.vertices:
                        points_list.append(wx.RealPoint(point[0], point[1]))
                    dc.DrawSpline(points_list)
                    
            plot.set_xlim( (-3, 3))
            plot.set_ylim( (-3, 0))
            #plot.set_frame_on(False)
            #adjust_spines(plot,[])
            plot.axis('off')
            canvas.draw()
            
            s = canvas.tostring_rgb()  # save this and convert to bitmap as needed
    
            l,b,w,h = fig.bbox.bounds
            w, h = int(w), int(h)
            
            # convert to a numpy array
            X = np.fromstring(s, np.uint8)
            X.shape = h, w, 3
            
            image = wx.EmptyImage(w,h)
            image.SetData(X.tostring())
            wxBitmap = image.ConvertToBitmap()
            contour_offset = self.size.width/100.0 * 10
            dc.DrawBitmap(wxBitmap, position.x - contour_offset, position.y+self.size.height)
            #dc.DrawBitmap(wxBitmap, position.x, position.y+self.size.height)
    
    def draw_contour(self, dc, position, orientation='RIGHT'):
        if self.ref_obj:
            
            A = 0
            K = 1
            B = 2
            Q = 0.01
            M = 0.01
            
            x1, y1 = 2,0
            x2, y2 = 8,0
            
            x_left_lim  = 0
            x_right_lim = 11
            y_left_lim  = 0
            y_right_lim = 4

            #delta = 1
            #x = np.arange(x_left_lim, x_right_lim, delta)
            #y = np.arange(y_left_lim, y_right_lim, delta)
            #X, Y = np.meshgrid(x, y)
            #Z = np.zeros((X.shape[0],X.shape[1]))

            x = linspace(x_left_lim, x_right_lim, 11)
            y = linspace(y_left_lim, y_right_lim, 4)
            X, Y = meshgrid(x, y)
            Z = np.zeros((X.shape[0],X.shape[1]))
            
            for i in range(y.shape[0]):
                for j in range(x.shape[0]):
                    ang = find_angle(x1,y1,x2,y2,x[j],y[i])
                    dist1 = distance(x1, y1, x[j], y[i])
                    dist2 = distance(x2, y2, x[j], y[i])
                    avg_dist = (dist1+dist2)/2
                    if avg_dist == 0:
                        avg_dist = 0.0000001
                    Z[i,j] = 4*gen_logistic(A, K, B, Q, M, ang) + 1/avg_dist

            targets = dict(left=0, right=0, top=0, bottom=0, hspace=30, wspace=30)
            
            if self.orientation == 'UP' or self.orientation == 'DOWN':
                fig_w = self.size.width/96.0
                fig_h = self.size.width/100.0
                contour_offset = self.size.width/100.0 * 10
            if self.orientation == 'LEFT' or self.orientation == 'RIGHT':
                fig_w = self.size.height/96.0
                fig_h = self.size.height/100.0
                contour_offset = self.size.height/100.0 * 10
                
            fig = Figure(figsize=(fig_w,fig_h), dpi=120,frameon=False)
            plot = fig.add_subplot(111)
            adjust_borders(fig, targets)

            canvas = FigureCanvasAgg(fig)
            
            if self.orientation == 'UP':
                #plot.contourf(X, Y, Z, levels,alpha=0.8)
                plot.contourf(X, Y, Z, alpha=0.8)
                plot.set_xlim( (x_left_lim, x_right_lim) )
                plot.set_ylim( (y_left_lim, y_right_lim) )            
            elif self.orientation == 'DOWN':
                #plot.contourf(X, Y, Z, levels,alpha=0.8)
                plot.contourf(X, Y, Z, alpha=0.8)
                plot.set_xlim( (x_left_lim, x_right_lim) )
                plot.set_ylim( (y_right_lim, y_left_lim) )
            elif self.orientation == 'RIGHT':
                #plot.contourf(Y, X, Z, levels,alpha=0.8)
                plot.contourf(Y, X, Z, alpha=0.8)
                plot.set_xlim( (y_left_lim, y_right_lim) )
                plot.set_ylim( (x_right_lim, x_left_lim) )
            elif self.orientation == 'LEFT':
                #plot.contourf(Y, X, Z, levels,alpha=0.8)
                plot.contourf(Y, X, Z, alpha=0.8)
                plot.set_xlim( (y_right_lim, y_left_lim) )
                plot.set_ylim( (x_left_lim, x_right_lim) )
                
            plot.axis('off')
            canvas.draw()
            
            # save this and convert to bitmap as needed
            s = canvas.tostring_rgb()
    
            l,b,w,h = fig.bbox.bounds
            w, h = int(w), int(h)
            
            # convert to a numpy array
            X = np.fromstring(s, np.uint8)
            X.shape = h, w, 3
            
            image = wx.EmptyImage(w,h)
            image.SetData(X.tostring())
            wxBitmap = image.ConvertToBitmap()
                        
            if self.orientation == 'UP':
                dc.DrawBitmap(wxBitmap, position.x - contour_offset, position.y - h)
            elif self.orientation == 'DOWN':
                dc.DrawBitmap(wxBitmap, position.x - contour_offset, position.y+self.size.height)
            elif self.orientation == 'RIGHT':
                dc.DrawBitmap(wxBitmap, position.x + self.size.width, position.y - contour_offset)
            elif self.orientation == 'LEFT':
                dc.DrawBitmap(wxBitmap, position.x - w, position.y - contour_offset)


    def doPropertyEdit(self, parent):
        getTextEditor()
        
    def _privateDraw(self, dc, position, selected):
        """ Private routine to draw this DrawingObject.

            'dc' is the device context to use for drawing, while 'position' is
            the position in which to draw the object.  If 'selected' is True,
            the object is drawn with selection handles.  This private drawing
            routine assumes that the pen and brush have already been set by the
            caller.
        """
        dc.DrawRectangle(position.x, position.y,
                         self.size.width, self.size.height)
        #dc.DrawText(self.objType + '_' + self.name, position.x+3, position.y+3)
        dc.DrawText(self.name, position.x+3, position.y+3)
        
        # Draw arrow to show the orientation 
        if self.orientation == 'DOWN':
            arrow_start = (position.x + self.size.width/2, position.y + self.size.height)
            arrow_end   = (arrow_start[0], arrow_start[1] + self.size.height/6) 
            left_wing_start  = (arrow_start[0] + self.size.width/10, arrow_start[1] + self.size.height/10)
            right_wing_start = (arrow_start[0] - self.size.width/10, arrow_start[1] + self.size.height/10) 
        if self.orientation == 'UP':
            arrow_start = (position.x + self.size.width/2, position.y)
            arrow_end   = (arrow_start[0], arrow_start[1] - self.size.height/6)
            left_wing_start  = (arrow_start[0] + self.size.width/10, arrow_start[1] - self.size.height/10)
            right_wing_start = (arrow_start[0] - self.size.width/10, arrow_start[1] - self.size.height/10) 
        if self.orientation == 'RIGHT':
            arrow_start = (position.x + self.size.width, position.y + self.size.height/2)
            arrow_end   = (arrow_start[0] + self.size.width/6, arrow_start[1])
            left_wing_start  = (arrow_start[0] + self.size.width/10, arrow_start[1] + self.size.height/10)
            right_wing_start = (arrow_start[0] + self.size.width/10, arrow_start[1] - self.size.height/10) 
        if self.orientation == 'LEFT':
            arrow_start = (position.x, position.y + self.size.height/2)
            arrow_end   = (arrow_start[0] - self.size.width/6, arrow_start[1])
            left_wing_start  = (arrow_start[0] - self.size.width/10, arrow_start[1] + self.size.height/10)
            right_wing_start = (arrow_start[0] - self.size.width/10, arrow_start[1] - self.size.height/10) 
            
        if self.orientation != None:    
            dc.DrawLine(arrow_start[0], arrow_start[1], arrow_end[0], arrow_end[1])
            dc.DrawLine(left_wing_start[0], left_wing_start[1], arrow_end[0], arrow_end[1])
            dc.DrawLine(right_wing_start[0], right_wing_start[1], arrow_end[0], arrow_end[1])
        
        if self.ref_obj:
            self.draw_contour(dc, position, self.orientation)
            #self.draw_contour_lines(dc, position, self.orientation)            
        

#----------------------------------------------------------------------------
class ToolPaletteToggleX(wx.ToggleButton):
    """ An icon appearing in the tool palette area of our sketching window.

        Note that this is actually implemented as a wx.Bitmap rather
        than as a wx.Icon.  wx.Icon has a very specific meaning, and isn't
        appropriate for this more general use.
    """

    def __init__(self, parent, iconID, iconName, toolTip, mode = wx.ITEM_NORMAL):
        """ Standard constructor.

            'parent'   is the parent window this icon will be part of.
            'iconID'   is the internal ID used for this icon.
            'iconName' is the name used for this icon.
            'toolTip'  is the tool tip text to show for this icon.
            'mode'     is one of wx.ITEM_NORMAL, wx.ITEM_CHECK, wx.ITEM_RADIO

            The icon name is used to get the appropriate bitmap for this icon.
        """
        bmp = wx.Bitmap("images/" + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP)
        bmpsel = wx.Bitmap("images/" + iconName + "IconSel.bmp", wx.BITMAP_TYPE_BMP)

        wx.ToggleButton.__init__(self, parent, iconID,
                                 size=(bmp.GetWidth()+1, bmp.GetHeight()+1)
                                 )
        self.SetLabel( iconName )
        self.SetToolTip(wx.ToolTip(toolTip))
        #self.SetBitmapLabel(bmp)
        #self.SetBitmapSelected(bmpsel)

        self.iconID     = iconID
        self.iconName   = iconName

class ToolPaletteToggle(GenBitmapToggleButton):
    """ An icon appearing in the tool palette area of our sketching window.

        Note that this is actually implemented as a wx.Bitmap rather
        than as a wx.Icon.  wx.Icon has a very specific meaning, and isn't
        appropriate for this more general use.
    """

    def __init__(self, parent, iconID, iconName, toolTip, mode = wx.ITEM_NORMAL):
        """ Standard constructor.

            'parent'   is the parent window this icon will be part of.
            'iconID'   is the internal ID used for this icon.
            'iconName' is the name used for this icon.
            'toolTip'  is the tool tip text to show for this icon.
            'mode'     is one of wx.ITEM_NORMAL, wx.ITEM_CHECK, wx.ITEM_RADIO

            The icon name is used to get the appropriate bitmap for this icon.
        """
        bmp = wx.Bitmap("images/" + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP)
        bmpsel = wx.Bitmap("images/" + iconName + "IconSel.bmp", wx.BITMAP_TYPE_BMP)

        GenBitmapToggleButton.__init__(self, parent, iconID, bitmap=bmp, 
                                       size=(bmp.GetWidth()+1, bmp.GetHeight()+1),
                                       style=wx.BORDER_NONE)

        self.SetToolTip(wx.ToolTip(toolTip))
        self.SetBitmapLabel(bmp)
        self.SetBitmapSelected(bmpsel)

        self.iconID     = iconID
        self.iconName   = iconName


class ToolPaletteButton(GenBitmapButton):
    """ An icon appearing in the tool palette area of our sketching window.

        Note that this is actually implemented as a wx.Bitmap rather
        than as a wx.Icon.  wx.Icon has a very specific meaning, and isn't
        appropriate for this more general use.
    """

    def __init__(self, parent, iconID, iconName, toolTip):
        """ Standard constructor.

            'parent'   is the parent window this icon will be part of.
            'iconID'   is the internal ID used for this icon.
            'iconName' is the name used for this icon.
            'toolTip'  is the tool tip text to show for this icon.

            The icon name is used to get the appropriate bitmap for this icon.
        """
        bmp = wx.Bitmap("images/" + iconName + "Icon.bmp", wx.BITMAP_TYPE_BMP)
        GenBitmapButton.__init__(self, parent, iconID, bitmap=bmp, 
                                 size=(bmp.GetWidth()+1, bmp.GetHeight()+1),
                                 style=wx.BORDER_NONE)
        self.SetToolTip(wx.ToolTip(toolTip))
        self.SetBitmapLabel(bmp)

        self.iconID     = iconID
        self.iconName   = iconName



#----------------------------------------------------------------------------

class ToolOptionIndicator(wx.Window):
    """ A visual indicator which shows the current tool options.
    """
    def __init__(self, parent):
        """ Standard constructor.
        """
        wx.Window.__init__(self, parent, -1, wx.DefaultPosition, wx.Size(52, 32))

        self.penColour  = wx.BLACK
        self.fillColour = wx.WHITE
        self.lineSize   = 1
        self.objType    = None

        # Win95 can only handle a 8x8 stipple bitmaps max
        #self.stippleBitmap = wx.BitmapFromBits("\xf0"*4 + "\x0f"*4,8,8)
        # ...but who uses Win95?
        self.stippleBitmap = wx.BitmapFromBits("\xff\x00"*8+"\x00\xff"*8,16,16)
        self.stippleBitmap.SetMask(wx.Mask(self.stippleBitmap))

        self.Bind(wx.EVT_PAINT, self.onPaint)


    def setPenColour(self, penColour):
        """ Set the indicator's current pen colour.
        """
        self.penColour = penColour
        self.Refresh()


    def setFillColour(self, fillColour):
        """ Set the indicator's current fill colour.
        """
        self.fillColour = fillColour
        self.Refresh()


    def setLineSize(self, lineSize):
        """ Set the indicator's current pen colour.
        """
        self.lineSize = lineSize
        self.Refresh()

    def setObjType(self, objType):
        """ Set the indicator's current obj type.
        """
        self.objType = objType
        self.Refresh()        

    def onPaint(self, event):
        """ Paint our tool option indicator.
        """
        dc = wx.PaintDC(self)
        dc.BeginDrawing()

        dc.SetPen(wx.BLACK_PEN)
        bgbrush = wx.Brush(wx.WHITE, wx.STIPPLE_MASK_OPAQUE)
        bgbrush.SetStipple(self.stippleBitmap)
        dc.SetTextForeground(wx.LIGHT_GREY)
        dc.SetTextBackground(wx.WHITE)
        dc.SetBrush(bgbrush)
        dc.DrawRectangle(0, 0, self.GetSize().width,self.GetSize().height)

        if self.lineSize == 0:
            dc.SetPen(wx.Pen(self.penColour, self.lineSize, wx.TRANSPARENT))
        else:
            dc.SetPen(wx.Pen(self.penColour, self.lineSize, wx.SOLID))
        dc.SetBrush(wx.Brush(self.fillColour, wx.SOLID))

        size = self.GetSize()
        ctrx = size.x/2
        ctry = size.y/2
        radius = min(size)//2 - 5
        dc.DrawCircle(ctrx, ctry, radius)

        dc.EndDrawing()


#----------------------------------------------------------------------------

class ExceptionHandler:
    """ A simple error-handling class to write exceptions to a text file.

        Under MS Windows, the standard DOS console window doesn't scroll and
        closes as soon as the application exits, making it hard to find and
        view Python exceptions.  This utility class allows you to handle Python
        exceptions in a more friendly manner.
    """

    def __init__(self):
        """ Standard constructor.
        """
        self._buff = ""
        if os.path.exists("errors.txt"):
            os.remove("errors.txt") # Delete previous error log, if any.


    def write(self, s):
        """ Write the given error message to a text file.

            Note that if the error message doesn't end in a carriage return, we
            have to buffer up the inputs until a carriage return is received.
        """
        if (s[-1] != "\n") and (s[-1] != "\r"):
            self._buff = self._buff + s
            return

        try:
            s = self._buff + s
            self._buff = ""

            f = open("errors.txt", "a")
            f.write(s)
            print s
            f.close()

            if s[:9] == "Traceback":
                # Tell the user than an exception occurred.
                wx.MessageBox("An internal error has occurred.\nPlease " + \
                             "refer to the 'errors.txt' file for details.",
                             "Error", wx.OK | wx.CENTRE | wx.ICON_EXCLAMATION)
            sys.exit()    

        except:
            pass # Don't recursively crash on errors.

#----------------------------------------------------------------------------

class SketchApp(wx.PySimpleApp):
    """ The main pySketch application object.
    """
    def OnInit(self):
        """ Initialise the application.
        """
        global _docList
        _docList = []

        if len(sys.argv) == 1:
            # No file name was specified on the command line -> start with a
            # blank document.
            frame = DrawingFrame(None, -1, "Untitled")
            frame.Centre()
            frame.Show(True)
            _docList.append(frame)
        else:
            # Load the file(s) specified on the command line.
            for arg in sys.argv[1:]:
                fileName = os.path.join(os.getcwd(), arg)
                if os.path.isfile(fileName):
                    frame = DrawingFrame(None, -1,
                                         os.path.basename(fileName),
                                         fileName=fileName)
                    frame.Show(True)
                    _docList.append(frame)

        return True

#----------------------------------------------------------------------------

def main():
    """ Start up the pySketch application.
    """
    global _app

   
    # Redirect python exceptions to a log file.

    sys.stderr = ExceptionHandler()

    # Create and start the pySketch application.

    _app = SketchApp(0)
    _app.MainLoop()


if __name__ == "__main__":
    main()


