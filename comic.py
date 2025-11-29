import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import requests
from bs4 import BeautifulSoup
import os
import threading
from datetime import datetime
import json
from urllib.parse import urljoin, urlparse

CONFIG_FILE = "comic_downloader_config.json"


class ComicDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Web Comic Downloader")
        self.root.geometry("700x600")
        self.root.minsize(600, 500)

        self.comics_config = {
            "XKCD": "https://xkcd.com/",
            "Dilbert": "https://dilbert.com/strip",
            "SMBC": "https://www.smbc-comics.com/",
            "The Oatmeal": "https://theoatmeal.com/",
            "Cyanide & Happiness": "https://explosm.net/comics/latest"
        }

        self.stop_event = threading.Event()

        self.setup_ui()
        self.load_config()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if self.download_btn.cget('state') == tk.DISABLED:
            if messagebox.askyesno("Confirm Exit", "A download is in progress. Do you want to stop it and exit?"):
                self.stop_event.set()
                self.root.destroy()
        else:
            self.root.destroy()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="🚀 Web Comic Downloader",
                                font=("Arial", 16, "bold"))
        title_label.pack(pady=10)

        comics_frame = ttk.LabelFrame(
            main_frame, text="Select Comics to Download", padding="10")
        comics_frame.pack(fill=tk.X, pady=10)

        self.comic_vars = {}
        for comic_name in self.comics_config.keys():
            var = tk.BooleanVar()
            self.comic_vars[comic_name] = var
            cb = ttk.Checkbutton(comics_frame, text=comic_name, variable=var)
            cb.pack(anchor=tk.W, side=tk.LEFT, padx=5,
                    pady=2)

        custom_and_options_frame = ttk.Frame(main_frame)
        custom_and_options_frame.pack(fill=tk.X, pady=5)

        custom_frame = ttk.LabelFrame(
            custom_and_options_frame, text="Custom Comic URL", padding="10")
        custom_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.custom_url = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_url,
                  width=35).pack(fill=tk.X, pady=5)
        ttk.Label(custom_frame, text="Enter URL for a comic (only image scraping is attempted)",
                  font=("Arial", 8), foreground="gray").pack()

        options_frame = ttk.LabelFrame(
            custom_and_options_frame, text="Download Options", padding="10")
        options_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        options_subframe = ttk.Frame(options_frame)
        options_subframe.pack(fill=tk.X)

        ttk.Label(options_subframe, text="💾 Save to:").pack(side=tk.LEFT)
        self.save_path = tk.StringVar(
            value=os.path.join(os.path.expanduser("~"), "Comics"))
        ttk.Entry(options_subframe, textvariable=self.save_path,
                  width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(options_subframe, text="Browse",
                   command=self.browse_folder).pack(side=tk.LEFT)

        max_comics_frame = ttk.Frame(options_frame)
        max_comics_frame.pack(fill=tk.X, pady=5)
        ttk.Label(max_comics_frame, text="Max comics per source:").pack(
            side=tk.LEFT)
        self.max_comics = tk.StringVar(value="10")
        ttk.Spinbox(max_comics_frame, from_=1, to=100,
                    textvariable=self.max_comics, width=5).pack(side=tk.LEFT, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)

        self.download_btn = ttk.Button(
            button_frame, text="⬇️ Start Download", command=self.start_download, style="Accent.TButton")
        self.download_btn.pack(side=tk.LEFT, padx=10)

        self.stop_btn = ttk.Button(
            button_frame, text="⏹️ Stop Download", command=self.stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(button_frame, text="🧹 Clear Log",
                   command=self.clear_log).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="📂 Open Folder",
                   command=self.open_folder).pack(side=tk.LEFT, padx=10)

        progress_frame = ttk.LabelFrame(
            main_frame, text="Download Progress & Log", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.progress_label = ttk.Label(
            progress_frame, text="Ready to download comics...")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        self.log_text = scrolledtext.ScrolledText(
            progress_frame, height=12, font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_path.set(folder)

    def open_folder(self):
        path = self.save_path.get()
        if os.path.exists(path):
            try:
                if os.name == 'nt':
                    os.startfile(path)
                elif os.uname().sysname == 'Darwin':
                    os.system(f'open "{path}"')
                else:
                    os.system(f'xdg-open "{path}"')
            except Exception as e:
                self.log_message(f"❌ Failed to open folder: {e}")

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.progress_label.config(text="Ready to download comics...")
        self.progress_bar["value"] = 0

    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    saved_config = json.load(f)
                    self.save_path.set(saved_config.get(
                        'save_path', self.save_path.get()))
            except Exception as e:
                self.log_message(f"⚠️ Could not load config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'save_path': self.save_path.get()}, f)
        except Exception as e:
            self.log_message(f"⚠️ Could not save config: {e}")

    def start_download(self):
        selected_comics = [name for name,
                           var in self.comic_vars.items() if var.get()]

        if not selected_comics and not self.custom_url.get().strip():
            messagebox.showwarning(
                "Warning", "Please select at least one comic or enter a custom URL")
            return

        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.clear_log()
        self.stop_event.clear()

        thread = threading.Thread(
            target=self.download_comics, args=(selected_comics,))
        thread.daemon = True
        thread.start()

    def stop_download(self):
        self.log_message("⚠️ Stopping download process...")
        self.stop_event.set()

    def download_comics(self, selected_comics):
        downloaded_count = 0

        try:
            total_comics = len(selected_comics)
            if self.custom_url.get().strip():
                total_comics += 1

            if total_comics == 0:
                self.log_message("No comics selected. Download finished.")
                return

            self.progress_bar["maximum"] = total_comics
            self.progress_bar["value"] = 0

            os.makedirs(self.save_path.get(), exist_ok=True)
            self.save_config()

            for comic_name in selected_comics:
                if self.stop_event.is_set():
                    break

                self.progress_label.config(text=f"Downloading {comic_name}...")
                self.log_message(f"=== Starting {comic_name} Download ===")

                success_count = self.download_single_comic(
                    comic_name, self.comics_config[comic_name])

                if success_count > 0:
                    downloaded_count += 1
                    self.log_message(
                        f"🎉 {comic_name} finished. Downloaded {success_count} comics.")

                self.progress_bar["value"] += 1
                self.root.update_idletasks()

            if self.custom_url.get().strip() and not self.stop_event.is_set():
                self.progress_label.config(text="Downloading custom comic...")
                self.log_message("=== Starting Custom Comic Download ===")

                custom_name = "Custom_Comic"
                success_count = self.download_single_comic(
                    custom_name, self.custom_url.get().strip())

                if success_count > 0:
                    downloaded_count += 1
                    self.log_message(
                        f"🎉 Custom Comic finished. Downloaded {success_count} comics.")

                self.progress_bar["value"] += 1
                self.root.update_idletasks()

            if not self.stop_event.is_set():
                final_message = f"Download complete! {downloaded_count} sources processed."
                self.progress_label.config(text=final_message)
                self.log_message(
                    f"=== Finished! {downloaded_count} sources successfully processed ===")
                messagebox.showinfo("Complete", final_message)
            else:
                self.progress_label.config(text="Download stopped by user.")
                self.log_message("Download process halted by user.")

        except Exception as e:
            self.log_message(f"❌ Critical Error during download: {str(e)}")
            messagebox.showerror(
                "Error", f"A critical error occurred: {str(e)}")
        finally:
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.stop_event.clear()

    def download_single_comic(self, comic_name, base_url):
        if self.stop_event.is_set():
            return 0

        max_downloads = 1
        try:
            max_downloads = int(self.max_comics.get())
        except ValueError:
            self.log_message(
                "Invalid value for Max comics. Using default (1).")

        comic_folder = os.path.join(self.save_path.get(
        ), comic_name.replace(' & ', '_').replace(' ', '_'))
        os.makedirs(comic_folder, exist_ok=True)

        if comic_name == "XKCD":
            return self.download_xkcd(comic_folder, max_downloads)
        elif comic_name == "Dilbert":
            return self.download_dilbert(comic_folder, base_url, max_downloads)
        elif comic_name == "SMBC":
            return self.download_smbc(comic_folder, base_url)
        elif comic_name == "The Oatmeal":
            return self.download_oatmeal(comic_folder, base_url, max_downloads)
        elif comic_name == "Cyanide & Happiness":
            return self.download_cyanide(comic_folder, base_url)
        else:
            return self.download_generic(comic_folder, base_url, max_downloads)

    def _download_image(self, img_url, filepath, filename, referer=None):
        if not img_url:
            return False

        if img_url.startswith('//'):
            img_url = 'https:' + img_url
        elif not urlparse(img_url).scheme:
            pass

        if os.path.exists(filepath):
            self.log_message(f"⏩ Already exists: {filename}")
            return True

        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            if referer:
                headers['Referer'] = referer

            img_response = requests.get(
                img_url, headers=headers, stream=True, timeout=10)
            img_response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    if self.stop_event.is_set():
                        f.close()
                        os.remove(filepath)
                        return False
                    f.write(chunk)

            self.log_message(f"✅ Downloaded: {filename}")
            return True
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ Failed to download image {img_url}: {e}")
            return False
        except Exception as e:
            self.log_message(f"❌ File operation error for {filename}: {e}")
            return False

    def download_xkcd(self, folder, max_downloads):
        if self.stop_event.is_set():
            return 0
        downloaded = 0
        try:
            response = requests.get("https://xkcd.com/info.0.json", timeout=10)
            response.raise_for_status()
            latest_num = response.json()["num"]

            for comic_num in range(latest_num, latest_num - max_downloads, -1):
                if self.stop_event.is_set():
                    break
                if comic_num in (404, 0):
                    continue

                try:
                    comic_url = f"https://xkcd.com/{comic_num}/info.0.json"
                    response = requests.get(comic_url, timeout=10)
                    response.raise_for_status()
                    comic_data = response.json()

                    img_url = comic_data.get("img")
                    title = comic_data.get("safe_title", f"comic_{comic_num}")

                    clean_title = "".join(c if c.isalnum() or c in (
                        ' ', '_') else '' for c in title).strip().replace(' ', '_')
                    filename = f"xkcd_{comic_num:04d}_{clean_title}.png"
                    filepath = os.path.join(folder, filename)

                    if self._download_image(img_url, filepath, filename):
                        downloaded += 1

                except requests.exceptions.HTTPError as e:
                    self.log_message(
                        f"⚠️ XKCD #{comic_num} not found or failed (HTTP Error: {e.response.status_code})")
                except Exception as e:
                    self.log_message(
                        f"❌ Failed to download XKCD #{comic_num}: {str(e)}")
                    continue

        except Exception as e:
            self.log_message(
                f"❌ XKCD download failed (Initial check): {str(e)}")

        return downloaded

    def download_dilbert(self, folder, base_url, max_downloads):
        if self.stop_event.is_set():
            return 0
        downloaded = 0
        current_url = base_url

        try:
            for _ in range(max_downloads):
                if self.stop_event.is_set():
                    break

                response = requests.get(current_url, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                comic_img = soup.find('img', class_='img-responsive img-comic')
                if not comic_img:
                    comic_img = soup.find('img', class_='img-comic')

                if not comic_img or not comic_img.get('src'):
                    self.log_message(
                        f"⚠️ Dilbert: Could not find comic image on {current_url}")
                    break

                img_url = comic_img['src']

                path_parts = urlparse(current_url).path.split('/')
                comic_date = path_parts[-1] if path_parts[-1] else path_parts[-2]

                ext = os.path.splitext(urlparse(img_url).path)[1]
                filename = f"dilbert_{comic_date}{ext}"
                filepath = os.path.join(folder, filename)

                if self._download_image(img_url, filepath, filename, referer=current_url):
                    downloaded += 1

                prev_link_element = soup.find(
                    'a', class_='btn btn-lg btn-default btn-comic-navigation')
                next_url = None

                if not prev_link_element:
                    prev_link = soup.find('a', {'rel': 'prev'})
                    if prev_link:
                        next_url = urljoin(base_url, prev_link.get('href'))
                else:
                    next_url = urljoin(base_url, prev_link_element.get('href'))

                if not next_url or next_url == current_url:
                    self.log_message(
                        "ℹ️ Reached the oldest comic accessible or navigation failed.")
                    break

                current_url = next_url

        except requests.exceptions.RequestException as e:
            self.log_message(
                f"❌ Dilbert download failed on {current_url}: {str(e)}")
        except Exception as e:
            self.log_message(
                f"❌ Dilbert download failed (General Error): {str(e)}")

        return downloaded

    def download_smbc(self, folder, base_url):
        if self.stop_event.is_set():
            return 0

        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            comic_img = soup.find('img', id='cc-comic')
            if comic_img and comic_img.get('src'):
                img_url = comic_img['src']
                ext = os.path.splitext(urlparse(img_url).path)[1]
                filename = f"smbc_latest{ext}"
                filepath = os.path.join(folder, filename)

                if self._download_image(img_url, filepath, filename):
                    return 1

            self.log_message(
                "⚠️ SMBC: Could not find the comic image on the main page.")
            return 0

        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ SMBC download failed: {str(e)}")
            return 0

    def download_cyanide(self, folder, base_url):
        if self.stop_event.is_set():
            return 0

        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            comic_img = soup.find('img', id='main-comic')
            if comic_img and comic_img.get('src'):
                img_url = comic_img['src']
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url

                ext = os.path.splitext(urlparse(img_url).path)[1]
                filename = f"cyanide_latest{ext}"
                filepath = os.path.join(folder, filename)

                if self._download_image(img_url, filepath, filename):
                    return 1

            self.log_message(
                "⚠️ Cyanide & Happiness: Could not find the comic image on the latest page.")
            return 0

        except requests.exceptions.RequestException as e:
            self.log_message(
                f"❌ Cyanide & Happiness download failed: {str(e)}")
            return 0

    def download_oatmeal(self, folder, base_url, max_downloads):
        if self.stop_event.is_set():
            return 0
        downloaded = 0

        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            images = soup.find_all('img')

            for img in images:
                if self.stop_event.is_set():
                    break
                img_url = img.get('src')

                if img_url and 'comics/' in img_url and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png']):

                    full_img_url = urljoin(base_url, img_url)

                    url_path_segment = urlparse(
                        full_img_url).path.split('/')[-1]
                    filename = f"oatmeal_{url_path_segment}"
                    filepath = os.path.join(folder, filename)

                    if self._download_image(full_img_url, filepath, filename, referer=base_url):
                        downloaded += 1
                        if downloaded >= max_downloads:
                            break

            if downloaded == 0:
                self.log_message(
                    "⚠️ The Oatmeal: Could not find reliable comic image links on the main page.")

            return downloaded

        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ The Oatmeal download failed: {str(e)}")
            return 0

    def download_generic(self, folder, base_url, max_downloads):
        if self.stop_event.is_set():
            return 0
        downloaded = 0

        try:
            response = requests.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            images = soup.find_all('img')

            for img in images:
                if self.stop_event.is_set():
                    break
                img_url = img.get('src')

                if img_url and any(ext in img_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']) and 'icon' not in img_url.lower() and 'logo' not in img_url.lower():

                    full_img_url = urljoin(base_url, img_url)

                    ext = os.path.splitext(urlparse(full_img_url).path)[1]
                    filename = f"comic_{downloaded+1:03d}{ext}"
                    filepath = os.path.join(folder, filename)

                    if self._download_image(full_img_url, filepath, filename, referer=base_url):
                        downloaded += 1
                        if downloaded >= max_downloads:
                            break

            if downloaded == 0:
                self.log_message(
                    "⚠️ Generic Scraper: Found no relevant images to download.")

            return downloaded

        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ Generic download failed: {str(e)}")
            return 0


def main():
    root = tk.Tk()

    try:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Accent.TButton', foreground='white',
                        background='#007BFF', font=('Arial', 10, 'bold'))
        style.map('Accent.TButton',
                  background=[('active', '#0056b3')],
                  foreground=[('disabled', 'gray')])
    except tk.TclError:
        pass

    app = ComicDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
