class DataSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._screen_size = None
            cls._fish_options = None
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
    def fish_options(self):
        return self._fish_options

    @fish_options.setter
    def fish_options(self, fish: list):
        self._fish_options = fish
