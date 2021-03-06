import pytube
from kivy.config import Config
Config.set('kivy','window_icon', 'images/icon.png')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('kivy', 'exit_on_escape', '0')
from kivy.app import App
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.floatlayout import FloatLayout
from kivy.base import EventLoop
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.animation import Animation
from easygui import filesavebox
import threading
from time import sleep
from subprocess import run
from urllib import error
from os import remove
from os import _exit
# Resize window and put it in the center of the screen
Window.size = (960, 740)
Window.left -= 80
Window.top -= 70
# Animations needed for the script
spin_anim = Animation(angle=7.5, duration=.15) + Animation(angle=-7.5, duration=.15) + Animation(angle=0, duration=.15)
title_fade_anim = Animation(color=(1, 0.84, 0, 0), duration=.5) + Animation(color=(1, 0.84, 0, 1), duration=.5)
duration_fade_anim = Animation(color=(0.92, 0.67, 0.2, 0), duration=.5) + Animation(color=(0.92, 0.67, 0.2, 1), duration=.5)

def calculate_length(seconds):
    """Given a time in seconds, this
    function calculates the hours, minutes and seconds
    and returns it as a string formatted accordingly."""
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds -= minutes * 60
    if hours:
        return str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)
    else:
        return str(minutes).zfill(2) + ":" + str(seconds).zfill(2)


def show_popup(class_name, title, error=True):
    # This function simply displays a popup message, taking its contents from class_name.
    if error:
        Popup(title=title, title_size="18sp", title_font="images\\Orbitron.ttf", title_align="center", title_color=[1,0,0,1], separator_color=[1,1,0,1], content=class_name(), size_hint=(.5, .2)).open()
    else:
        Popup(title=title, title_size="18sp", title_font="images\\Orbitron.ttf", title_align="center", title_color=[0,1,0,1], separator_color=[1,1,0,1], content=class_name(), size_hint=(.5, .2)).open()


class WindowManager(ScreenManager):
    pass


class SearchPanel(Screen):
    url = ObjectProperty(None)
    search_button = ObjectProperty(None)

    def __init__(self, **kwargs):
        self.video = None
        self.clicked = True
        super(SearchPanel, self).__init__(**kwargs)
        self._keyboard = self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'f8':
            if self.manager.current == "search":
                self.manager.current = "secret"
            else:
                self.manager.current = "search"

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def search_video_start_thread(self, instance):
        if instance.text != "LOADING VIDEO...": spin_anim.start(instance)
        threading.Thread(target=self.search_video).start()
        Clock.schedule_interval(self.change_panel, .2)

    def search_video(self):
        """This function tries to create the YouTube object
        and popups an error message if something went wrong."""
        if self.clicked:
            self.search_button.text = "LOADING VIDEO..."
            self.search_button.background_down = ""
            self.clicked = False
            try:
                self.video = pytube.YouTube(self.url.text)
            except pytube.exceptions.RegexMatchError:
                self.clicked = True
                self.search_button.text = "SEARCH"
                self.search_button.background_down = "images/red.png"
                show_popup(URLError, "URL Error")
            except:
                self.clicked = True
                self.search_button.text = "SEARCH"
                self.search_button.background_down = "images/red.png"
                show_popup(Error, "Server Error")

    def change_panel(self, dt):
        # This function just transitions from the first panel to the second panel.
        # I need this in a separate function as Kivy cannot make transitions happen in a secondary thread.
        if self.video:
            Clock.unschedule(self.change_panel)
            self.parent.current = "videoinfo"


class VideoPanel(Screen):
    url = ObjectProperty(None)
    title = ObjectProperty(None)
    video_length = ObjectProperty(None)
    search_button = ObjectProperty(None)
    spinner = ObjectProperty(None)
    spinner_image = ObjectProperty(None)
    resolutions = ["2160p", "1440p", "1080p", "720p", "480p", "360p", "144p"]

    def on_pre_enter(self):
        self.clicked = True
        self.selected_videos = None
        self.path = None
        self.url.text = self.search.url.text
        self.modify_labels(animation=False)
        self.display_options()

    def search_video_start_thread(self):
        if self.search_button.text != "LOADING VIDEO...": spin_anim.start(self.search_button)
        threading.Thread(target=self.search_video).start()

    def search_video(self):
        # Same as before, but with more options.
        if self.clicked:
            self.search_button.text = "LOADING VIDEO..."
            self.search_button.background_down = ""
            self.clicked = False
            try:
                self.search.video = pytube.YouTube(self.url.text)
                self.selected_videos = None
                self.modify_labels()
                self.display_options()
                self.clicked = True
                self.modify_button()
            except pytube.exceptions.RegexMatchError:
                self.clicked = True
                self.modify_button()
                show_popup(URLError, "URL Error")
            except:
                self.clicked = True
                self.modify_button()
                show_popup(Error, "Server Error")

    def modify_labels(self, animation=True):
        # This function modifies labels when clicking the search button.
        if animation:
            title_fade_anim.start(self.title)
            duration_fade_anim.start(self.video_length)
            sleep(.5)
        self.title.text = self.search.video.title
        self.title.font_size = str(1700 / len(self.title.text)) + "sp" if 1700/len(self.title.text) <= 65 else "65sp"
        self.video_time = calculate_length(self.search.video.length)
        self.video_length.text = f"DURATION: {self.video_time}"

    def display_options(self):
        # This function attaches all the possible resolution as options in the spinner object.
        self.spinner.values.clear()
        self.spinner.text = ""
        self.spinner_image.opacity = 1
        self.spinner.values = [resolution for resolution in self.resolutions if self.search.video.streams.filter(res=resolution)]
        self.spinner.values.append("AUDIO")

    def modify_button(self):
        # This function modifies the search button accordingly.
        self.search_button.text = "SEARCH AGAIN"
        self.search_button.background_down = "images/red.png"

    def get_value_start_thread(self, instance):
        if self.spinner.text: spin_anim.start(instance)
        threading.Thread(target=self.get_value).start()

    def get_value(self):
        """This function appends the selected videos to the selected_videos list.
        Pytube can't download both video and audio in the same file,
        so if the user choose a video format, this function will append 2 values
        in the selected_videos list: the video with the selected resolution and the video audio.
        It just appends the audio if the user choose the audio format."""
        self.selected_videos = []
        if self.spinner.values:
            self.spinner_image.opacity = 0
            if self.spinner.text[0].isdigit():
                # Some resolutions (360p and 144p) also have the audio included, but for some reason their size are huge, so always choose the non-audio video and later merge it with the audio file.
                if not self.search.video.streams.filter(res=self.spinner.text)[0].includes_audio_track:
                    self.selected_videos = [self.search.video.streams.filter(res=self.spinner.text)[0]]
                else:
                    self.selected_videos = [self.search.video.streams.filter(res=self.spinner.text)[1]]
            self.selected_videos.append(self.search.video.streams.filter(only_audio=True)[1])
            try: self.total_size = sum([video.filesize for video in self.selected_videos])
            except (error.URLError, error.HTTPError):
                # In case of HTTP error, change spinner text and remove the option.
                self.total_size = 0
                self.spinner.values.remove(self.spinner.text)
                self.spinner.text = self.spinner.values[0]
            self.video_length.text = f"DURATION: {self.video_time} - SIZE: {round(self.total_size / 1024 ** 2, 2)}MB"

    def download(self):
        """This function stores in a variable the user's desired path and adds the extension to the file if it is not included in the name.
        If the user hasn't chosen any resolution, the spinner options will be shown. """
        if self.selected_videos:
            extension = ".mp4" if len(self.selected_videos) > 1 else ".mp3"
            self.path = filesavebox("Select download directory", "YouTube Downloader", self.title.text + extension)
            if self.path:
                if not self.path.endswith(extension): self.path += extension
                self.path = "\\".join(self.path.split("\\")[:-1]) + '\\\\"' + self.path.split("\\")[-1] + '"'
                self.parent.current = "download"
        else:
            self.spinner.is_open = True


class DownloadPanel(Screen):
    progressbar = ObjectProperty(None)
    mb_remaining = ObjectProperty(None)
    percentage = ObjectProperty(None)
    pause_button_image = ObjectProperty(None)
    back_button = ObjectProperty(None)

    def on_pre_enter(self):
        """Starts the download of the files.
        Stores the video and the audio in different files with no extension,
        they will later be merged in a single file with the desired path."""
        self.video_path = "\\".join(self.videoinfo.path.split("\\")[:-1]) + "\\temp_file1"
        self.audio_path = "\\".join(self.videoinfo.path.split("\\")[:-1]) + "\\temp_file2"
        self.pause_button_image.source = "images/pause.png"
        self.back_button.disabled = True
        self.paused = False
        self.cancelled = False
        self.is_downloading = True
        self.thread = threading.Thread(target=self.download_video)
        self.thread.start()

    def download_video(self):
        # Downloads the video chunk by chunk, to let the user pause or cancel the download.
        # Also displays the download progress by changing the progressbar value and modifying labels.
        self.progressbar.max = self.videoinfo.total_size
        self.progressbar.value = 0
        downloaded = 0
        for file in self.videoinfo.selected_videos:
            if len(self.videoinfo.selected_videos) > 1:
                path = self.audio_path if file.includes_audio_track else self.video_path
            else:
                path = self.videoinfo.path.replace('"', '')
            with open(path, "wb") as f:
                stream = pytube.request.stream(file.url)
                while not self.cancelled:
                    if self.paused:
                        sleep(.25)
                        continue
                    chunk = next(stream, None)
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progressbar.value = downloaded
                        self.mb_remaining.text = f"{round(downloaded / 1024 ** 2, 2)}MB / {round(self.videoinfo.total_size / 1024 ** 2, 2)}MB"
                        self.percentage.text = f"{round(downloaded * 100 / self.videoinfo.total_size, 2)}%"
                        continue
                    # If the download has ended, merge the files if they are more than two, open the success popup and activate the back button.
                    if self.percentage.text == "100.0%":
                        self.is_downloading = False
                        if len(self.videoinfo.selected_videos) > 1:
                            threading.Thread(target=self.merge_videos).start()
                        else:
                            show_popup(Success, "Download Sucessful", error=False)
                            self.back_button.disabled = False
                    break

    def pause_download(self):
        # Change the pause button icon and pause the video.
        self.pause_button_image.source = "images/pause.png" if self.paused else "images/resume.png"
        self.paused = not self.paused

    def open_popup(self):
        # Open a customized popup if the user wants to cancel the download while the files are downloading.
        if self.is_downloading:
            self.confirmation_popup = Popup(title="!    !   !", title_size="30sp", title_font="images\\Orbitron.ttf", title_align="center", title_color=[1,0,0,1], separator_color=[1,1,0,1], content=ConfirmationCancel(), size_hint=(.5, .5), auto_dismiss=False)
            self.confirmation_popup.open()

    def cancel_download(self):
        # Cancel the download and delete all the temporary files that have been downloaded.
            self.cancelled = True
            self.is_downloading = False
            self.thread.join()
            self.delete_files()
            try: remove(self.videoinfo.path.replace('"', ''))
            except FileNotFoundError: pass
            self.progressbar.value = 0
            self.mb_remaining.text = "Download Cancelled"
            self.back_button.disabled = False

    def dismiss(self):
        # Dismiss the popup.
        self.confirmation_popup.dismiss()

    def merge_videos(self):
        # Merge temporary files using ffmpeg without opening the console, deletes the temporary files after and displays the success popup.
        # Displays a customized popup error if ffmepg is not installed.
        self.thread.join()
        try:
            run(f"ffmpeg -y -i {self.video_path} -i {self.audio_path} -c copy {self.videoinfo.path}", creationflags=0x08000000)
            success = True
        except FileNotFoundError:
            show_popup(FFMPEGError, "FFMPEG not found")
            success = False
        self.delete_files()
        self.back_button.disabled = False
        if success:
            show_popup(Success, "Download Sucessful", error=False)

    def delete_files(self):
        # Delete all the temporary files that have been downloaded.
        try:
            remove(self.video_path)
            remove(self.audio_path)
        except FileNotFoundError: pass


class Secret(Screen):
    def __init__(self, **kwargs):
        super(Secret, self).__init__(**kwargs)

    def on_enter(self):
        self._keyboard = self.searchscreen._keyboard


class RightClickTextInput(TextInput):
    # Open the bubble menu "copy, cut, paste" on right click on a TextInput object.
    def on_touch_down(self, touch):
        super(RightClickTextInput,self).on_touch_down(touch)
        if touch.button == 'right':
            try:
                pos = super(RightClickTextInput, self).to_local(*self._long_touch_pos, relative=False)
                self._show_cut_copy_paste(pos, EventLoop.window)
            except AttributeError: pass


class URLError(FloatLayout):
    pass


class Error(FloatLayout):
    pass


class FFMPEGError(FloatLayout):
    pass


class Success(FloatLayout):
    pass


class ConfirmationCancel(FloatLayout):
    pass


class ConfirmationQuit(FloatLayout):
    pass


kv = Builder.load_file("design.kv")


class MyApp(App):
    App.title = "PyTube Downloader"

    def build(self):
        Window.bind(on_request_close=self.on_request_close)
        return kv

    def on_request_close(self, *args):
        # Displays a popup if the users wants to close the application while the files are downloading.
        if App.get_running_app().root.current == "download":
            if App.get_running_app().root.current_screen.is_downloading:
                self.confirmation_popup = Popup(title="!    !    !", title_size="30sp", title_font="images\\Orbitron.ttf", title_align="center", title_color=[1,0,0,1], separator_color=[1,1,0,1], content=ConfirmationQuit(), size_hint=(.5, .5), auto_dismiss=False)
                self.confirmation_popup.open()
                return True

    def cancel(self):
        # Dismiss the popup.
        self.confirmation_popup.dismiss()

    def exit(self):
        # Deletes the files and closes the application.
        App.get_running_app().root.current_screen.cancel_download()
        _exit(0)


if __name__ == "__main__":
    MyApp().run()
