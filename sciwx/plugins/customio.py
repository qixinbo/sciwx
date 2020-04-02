from sciwx.action import SciAction, ImgAction
from skimage.io import imread, imsave
import numpy as np

class Open(SciAction):
    name = 'Open'
    def start(self, app, para=None):
        path = app.getpath('Open', ['png','bmp','jpg'], 'open')
        if path is None: return
        img = imread(path)
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

        app.show_img(img)

class Save(ImgAction):
    name = 'Save'
    para = {'path':''}

    def show(self):
        path = self.app.getpath('Open', ['png','bmp','jpg'], 'save')
        if path is None: return
        self.para['path'] = path
        return True

    def run(self, ips, img, snap, para):
        imsave(para['path'], img)