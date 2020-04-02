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
# from sciwx.plugins.setscale import SetScale
from sciwx.plugins.aibrush import AIBrush
from sciwx.plugins.io import Open, Save

from sciwx.widgets import ParaDialog
from sciwx.manager import ConfigManager

import numpy as np
from skimage.filters import threshold_otsu, sobel
import scipy.ndimage as ndimg
from scipy.ndimage import label, generate_binary_structure
from skimage.measure import regionprops
from skimage.graph import route_through_array
from skimage.io import imsave


def ExtractUpperBoundary(img):
    print('img dim = ', img.ndim)

    # uint8 conversion
    if img.ndim > 2:
        img = img.mean(axis=2).astype(np.uint8)
    else:
        img = img.astype(np.uint8)

    # crop to remove the noisy boundaries
    print('img shape before crop = ', img.shape)
    margin = 3
    img = img[margin:img.shape[0]-margin, margin:img.shape[1]-margin]
    print('img shape after crop = ', img.shape)

    # make a copy for lower boundary classification
    snap = img.copy()

    # otsu threshold
    img = (img > threshold_otsu(img))*255
    ndimg.binary_fill_holes(img, output=img)
    img *= 255

    # Geometry filter
    struc = generate_binary_structure(2, 1) # 4-connect
    lab, n = label(img, struc, output=np.uint32)
    idx = (np.ones(n+1)*255).astype(np.uint8)
    ls = regionprops(lab)
    for i in ls:
        if i.area < 2000:
            idx[i.label] = 0
    idx[0] = 0
    img = idx[lab]

    # sobel 
    img = sobel(img)
    # Second round of geometry filter
    struc = generate_binary_structure(2, 2) # 8-connect
    lab, n = label(img, struc, output=np.uint32)
    idx = (np.ones(n+1)*255).astype(np.uint8)
    ls = regionprops(lab)
    for i in ls:
        if i.area < 2000:
            idx[i.label] = 0
    idx[0] = 0
    img = idx[lab]

    # find the corners
    idx_white = np.argwhere(img > 0)

    fake_left_point = [img.shape[0]*2, img.shape[1]*1.5/4]
    fake_right_point = [img.shape[0]*2, img.shape[1]*3/4]

    idx_left_corner = np.argmin(np.linalg.norm(idx_white - fake_left_point, axis=1))
    idx_right_corner = np.argmin(np.linalg.norm(idx_white - fake_right_point, axis=1))
    pt_left = idx_white[idx_left_corner]
    pt_right = idx_white[idx_right_corner]
    print('idx of left corner = ', pt_left)
    print('idx of right corner = ', pt_right)

    # find the up vertex
    pt_up = idx_white[0]
    print('up vertex idx = ', pt_up)

    # adjust the grey value
    max_value = 170
    snap[snap < max_value] = max_value

    # DOG operation to make the lower boundary clear
    ndimg.gaussian_filter(snap, 0.0, output=snap)
    buf = ndimg.gaussian_filter(snap, 3.0, output=snap.dtype)
    snap -= buf
    np.add(snap, np.mean((0, 255)), out=snap, casting='unsafe')

    # route programming
    cost = 0.0
    np.add(snap, cost-snap.min(), casting='unsafe', out=snap)
    indices, weight = route_through_array(snap, pt_left, pt_right)
    rs, cs = np.vstack(indices).T
    snap[rs, cs] = 255

    # find the down vertex
    pt_down = np.argwhere(snap == 255)[-1]
    print('down vertex idx = ', pt_down)

    return pt_left, pt_right, pt_up, pt_down, snap

def make_mark(p0, p1, p2, p3, img):
    p_middle_x = (p0[0] + p1[0])/2
    line_middle_horizon = [(0, p_middle_x), (img.shape[1], p_middle_x)]
    line_up_horizon = [(0, p2[0]), (img.shape[1], p2[0])]
    line_down_horizon = [(0, p3[0]), (img.shape[1], p3[0])]
    line_left_verizon = [(p0[1], 0), (p0[1], img.shape[0])]
    line_right_verizon = [(p1[1], 0), (p1[1], img.shape[0])]

    lines = {'type':'lines', 'color':(0,255,0), 'lw':2, 'style':'-', 
    'body':[line_middle_horizon,
            line_up_horizon,
            line_down_horizon,
            line_left_verizon,
            line_right_verizon]}

    lenght_height_x = (p1[0]+p2[0])/2-10
    lenght_height_y = p1[1]+10
    height = p_middle_x-p2[0]
    height_text = str(height)

    texts = {'type':'texts', 'color':(255,255,0), 'fcolor':(0,0,0), 'size':20, 'pt':False, 
    'body':[(lenght_height_y, lenght_height_x, height_text),
            (180,250,'id=1')]}

    mark = {'type':'layer', 'body':[lines, texts]}
    return mark

class ExtractMeltPool(Tool):
    """ColorPicker class plugin with events callbacks"""
    title = 'Extract Melt Pool'
    
    def __init__(self):
        self.status_enabled = False
        self.pos = []

    def mouse_down(self, ips, x, y, btn, **key):
        if btn == 1:
            self.status_enabled = True
            self.pos.append((y, x))
    
    def mouse_up(self, ips, x, y, btn, **key):
        if len(self.pos) == 2:
            print("pos = ", self.pos)
            para = {'scalebar': 200}
            view = [('lab', 'lab', 'Please input the real length the scale bar'),
            (int, 'scalebar', (0, 1000), 1, 'Length', 'um')]
            pd = ParaDialog(None, 'Scale bar')
            pd.init_view(view, para, preview=False, modal=True)
            pd.ShowModal()
            ConfigManager.set('scalebar', para['scalebar']/(self.pos[1][1]-self.pos[0][1]))
            print(ConfigManager.get('scalebar'))
            pt_left, pt_right, pt_up, pt_down, ips.img = ExtractUpperBoundary(ips.img)
            key['canvas'].marks = make_mark(pt_left, pt_right, pt_up, pt_down, ips.img)['body']
            ips.update()
            self.pos = []

    
    def mouse_move(self, ips, x, y, btn, **key):
        pass
        
    def mouse_wheel(self, ips, x, y, d, **key):
        pass


class MeltPoolApp(wx.Frame, App):
    def __init__( self, parent ):
        wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = 'MeltPoolApp', 
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
    frame = MeltPoolApp(None)
    frame.load_menu(('menu',[('File',[('Open', Open),
                                      ('Save', Save)]),
                             ('Edit', [('Gaussian', Gaussian),
                                          ('Undo', Undo)])]))
    frame.load_tool(('tools',[('standard', [('D', DefaultTool),
                                            ('S', ExtractMeltPool)]),
                              ('draw', [('P', Pencil),
                                        ('A', AIBrush)])]))

    frame.Show()

    app.MainLoop()
