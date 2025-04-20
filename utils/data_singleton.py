from .consts import DISPLAY_RESIZE_WIRDS

class DataSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataSingleton, cls).__new__(cls)
            cls._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._screen_size = None
        self._full_display_size = None
        self._img_resize = None
        self._vocab_font = None
        self._espeak_engine = None
        self._env = None
        self._is_spin = None
        self._window = None
        self._initialized = True

    @property
    def window_size(self):
        return self._screen_size

    @window_size.setter
    def window_size(self, size):
        if isinstance(size, tuple) and len(size) == 2:
            self._full_display_size = size
            self._screen_size = (DISPLAY_RESIZE_WIRDS, int(size[1] / (size[0] / DISPLAY_RESIZE_WIRDS)))
        else:
            raise ValueError("Screen size must be a tuple of two integers")
        
    @property
    def full_display_size(self): return self._full_display_size
        
    @property
    def img_resize(self):
        return self._img_resize

    @img_resize.setter
    def img_resize(self, size):
        if isinstance(size, tuple) and len(size) == 2:
            self._img_resize = size
        else:
            raise ValueError("Image size must be a tuple of two integers")

    @property
    def vocab_font(self):
        return self._vocab_font

    @vocab_font.setter
    def vocab_font(self, font):
        if self._vocab_font is None: self._vocab_font = font
    
    @property
    def espeak_engine(self):
        return self._espeak_engine

    @espeak_engine.setter
    def espeak_engine(self, eng):
        if self._espeak_engine is None: self._espeak_engine = eng

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, env):
        if self._env is None: self._env = env

    @property
    def is_spin(self):
        return self._is_spin

    @is_spin.setter
    def is_spin(self, is_spin):
        self._is_spin = bool(int(is_spin))

    @property
    def window(self):
        return self._window
    
    @window.setter
    def window(self, window):
        self._window = window
