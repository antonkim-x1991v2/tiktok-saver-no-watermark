# tiktok-saver-no-watermark

I needed a reliable way to archive some TikTok videos locally without those annoying watermarks bouncing around the screen. Most online tools are covered in ads and captcha prompts, and the existing scrapers I found were bloated or broken because of TikTok's constant layout changes. 

This is a simple command line tool that takes a TikTok video URL, resolves the direct download link, and saves it to your drive.

## Installation

Clone the repository and install the dependencies. I recommend using a virtual environment.

```cmd
pip install -r requirements.txt
```

## Usage

Pass the video URL directly to the script. It works with both standard and short share links (e.g. `vm.tiktok.com`).

```cmd
python saver.py "https://www.tiktok.com/@username/video/1234567890123456789"
```

By default, files are saved in the current directory. You can specify a custom output directory using the `-o` or `--out` option:

```cmd
python saver.py "https://vt.tiktok.com/ZS12345/" -o "D:\Media\Archived"
```

If you want to silence the console output and just get the file path on success, use the `--quiet` flag.

<!-- refreshed: 2026-09-22 -->
