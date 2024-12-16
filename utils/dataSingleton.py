class DataSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._screen_size = None
            cls._img_resize = None
            cls._fish_options = None
            cls._vocab_options = None
            cls._vocab_font = None
            cls._espeak_engine = None
            cls._env = None
        return cls._instance

    @property
    def window_size(self):
        return self._screen_size

    @window_size.setter
    def window_size(self, size):
        if isinstance(size, tuple) and len(size) == 2:
            self._screen_size = size
        else:
            raise ValueError("Screen size must be a tuple of two integers")
        
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
    def vocab_options(self):
        return self._vocab_options

    @vocab_options.setter
    def vocab_options(self, vocab: list):
        self._vocab_options = vocab

    @property
    def vocab_font(self):
        return self._vocab_font

    @vocab_font.setter
    def vocab_font(self, font):
        self._vocab_font = font
    
    @property
    def espeak_engine(self):
        return self._espeak_engine

    @espeak_engine.setter
    def espeak_engine(self, eng):
        self._espeak_engine = eng

    @property
    def env(self):
        return self._env

    @env.setter
    def env(self, env):
        self._env = env
