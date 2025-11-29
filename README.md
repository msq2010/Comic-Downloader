### 📚 Web Comic Downloader 

A simple, multi-threaded, and platform-independent **GUI application** built with **Python's Tkinter, `requests`, and `BeautifulSoup`** to download webcomics from pre-configured or custom URLs.

#### ✨ Features

* **GUI Interface:** Easy-to-use graphical interface for selection and control.
* **Multi-threaded:** Downloads run in a separate thread, keeping the GUI responsive.
* **Pre-configured Comics:** Built-in support for popular comics:
    * **XKCD** (Uses JSON API for efficient batch downloading)
    * **Dilbert** (Scrapes sequential strips)
    * **SMBC**
    * **The Oatmeal**
    * **Cyanide & Happiness**
* **Download Limits:** Specify the maximum number of comics to retrieve for each source.
* **Custom URL Support:** Allows attempting to scrape images from any user-provided URL.
* **Persistent Configuration:** Saves the last used download folder path.
* **Download Log:** Detailed, time-stamped log of the download process.

***

#### ⚙️ Prerequisites

You must have **Python 3.x** installed. The application uses the following libraries:

1.  `tkinter` (Usually included with standard Python installations)
2.  `requests`
3.  `beautifulsoup4`

#### 💻 Installation

1.  **Clone or download** the code (e.g., save the Python script as `comic_downloader.py`).
2.  **Install dependencies** using `pip`:

    ```bash
    pip install requests beautifulsoup4
    ```

***

#### ▶️ How to Run

Execute the Python script from your terminal:

```bash
python comic_downloader.py