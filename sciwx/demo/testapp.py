import sys
sys.path.append('../../')

import wx, os, sys
import time, threading

import wx.lib.agw.aui as aui
from sciwx.widgets import MenuBar, ToolBar
from sciwx.canvas import CanvasNoteBook
from sciwx.app.manager import App

from sciwx.action import Tool, DefaultTool

from sciwx.plugins.filters import Gaussian, Undo
from sciwx.plugins.pencil import Pencil
from sciwx.plugins.colorpicker import ColorPicker
from sciwx.plugins.aibrush import AIBrush
from sciwx.plugins.io import Open, Save

class TestApp(wx.Frame, App):
    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = 'TestApp', 
                            size = wx.Size(-1,-1), pos = wx.DefaultPosition, 
                            style = wx.RESIZE_BORDER|wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )
        App.__init__(self)
        self.auimgr = aui.AuiManager()
        self.auimgr.SetManagedWindow(self)
        self.SetSizeHints(wx.Size(1024,768))
        
        self.init_menu()
        self.init_tool()
        self.init_canvas()

        self.Layout()
        self.auimgr.Update()
        self.Fit()
        self.Centre(wx.BOTH)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_pan_close)
        
    def load_menu(self, data):
        self.menubar.load(data)

    def load_tool(self, data, default=None):
        for i, (name, tols) in enumerate(data[1]):
            self.toolbar.add_tools(name, tols, i==0)
        if not default is None: self.toolbar.add_pop('P', default)
        self.toolbar.Layout()
        
    def init_menu(self):
        self.menubar = MenuBar(self)
        
    def init_tool(self):
        self.toolbar = ToolBar(self, True)

        self.auimgr.AddPane(self.toolbar, aui.AuiPaneInfo() .Left()  .PinButton( True )
            .CaptionVisible( True ).Dock().Resizable().FloatingSize( wx.DefaultSize ).MaxSize(wx.Size( 32,-1 ))
            . BottomDockable( True ).TopDockable( False ).Layer( 10 ) )
        
    def init_canvas(self):
        self.canvasnbwrap = wx.Panel(self)
        sizer = wx.BoxSizer( wx.VERTICAL )
        self.canvasnb = CanvasNoteBook( self.canvasnbwrap)
        sizer.Add( self.canvasnb, 1, wx.EXPAND |wx.ALL, 0 )
        self.canvasnbwrap.SetSizer( sizer )
        self.canvasnbwrap.Layout()
        self.auimgr.AddPane( self.canvasnbwrap, aui.AuiPaneInfo() .Center() .CaptionVisible( False ).PinButton( True ).Dock()
            .PaneBorder( False ).Resizable().FloatingSize( wx.DefaultSize ). BottomDockable( True ).TopDockable( False )
            .LeftDockable( True ).RightDockable( True ) )
        self.canvasnb.Bind( wx.lib.agw.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_new_img)
        self.canvasnb.Bind( wx.lib.agw.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_img)

    def on_pan_close(self, event):
        if event.GetPane().window in [self.toolbar, self.widgets]:
            event.Veto()
        if hasattr(event.GetPane().window, 'close'):
            event.GetPane().window.close()

    def on_new_img(self, event):
        self.add_img_win(self.canvasnb.canvas())
        self.add_img(self.canvasnb.canvas().image)

    def on_close_img(self, event):
        canvas = event.GetEventObject().GetPage(event.GetSelection())
        self.remove_img_win(canvas)
        self.remove_img(canvas.image)

    def on_close(self, event):
        print('close')
        #ConfigManager.write()
        self.auimgr.UnInit()
        del self.auimgr
        self.Destroy()
        sys.exit()

    def show_img(self, img):
        canvas = self.canvasnb.add_canvas()
        canvas.set_img(img)
        self.add_img_win(canvas)
        self.add_img(canvas.image)

    def alert(self, info, title='SciWx'):
        dialog=wx.MessageDialog(self, info, title, wx.OK)
        dialog.ShowModal() == wx.ID_OK
        dialog.Destroy()

    def getpath(self, title, filt, io, name=''):
        filt = '|'.join(['%s files (*.%s)|*.%s'%(i.upper(),i,i) for i in filt])
        dic = {'open':wx.FD_OPEN, 'save':wx.FD_SAVE}
        dialog = wx.FileDialog(self, title, '', name, filt, dic[io])
        rst = dialog.ShowModal()
        path = dialog.GetPath() if rst == wx.ID_OK else None
        dialog.Destroy()
        return path

if __name__ == '__main__':
    app = wx.App(False)
    frame = TestApp(None)
    frame.load_menu(('menu',[('File',[('Open', Open),
                                      ('Save', Save)]),
                             ('Edit', [('Gaussian', Gaussian),
                                          ('Undo', Undo)])]))
    frame.load_tool(('tools',[('standard', [('D', DefaultTool),
                                            ('C', ColorPicker)]),
                              ('draw', [('P', Pencil),
                                        ('A', AIBrush)])]))

    frame.Show()

    app.MainLoop()
