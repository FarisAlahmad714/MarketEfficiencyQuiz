import cv2
import pytesseract
import os
import re
import numpy as np

class CandleAnalyzer:
    def __init__(self, static_folder):
        self.static_folder = static_folder
        
    def validate_sequence(self, setup_file, outcome_file):
        """
        Validates the sequence of setup and outcome images by comparing their closing prices.

        Args:
            setup_file (str): Path to the setup image file.
            outcome_file (str): Path to the outcome image file.

        Returns:
            str: "Bullish", "Bearish", or "Unknown".
        """
        setup_path = os.path.join(self.static_folder, setup_file)
        outcome_path = os.path.join(self.static_folder, outcome_file)

        # Extract closing prices and dates from both images
        setup_close = self.extract_closing_price(setup_path)
        outcome_close = self.extract_closing_price(outcome_path)
        setup_date = self.extract_date(setup_path)
        outcome_date = self.extract_date(outcome_path)

        # Debug: Print extracted closing prices and dates
        print(f"\n=== Setup Image ===")
        print(f"Date: {setup_date}")
        print(f"Closing Price: {setup_close}")

        print(f"\n=== Outcome Image ===")
        print(f"Date: {outcome_date}")
        print(f"Closing Price: {outcome_close}")

        # Compare closing prices to determine bias
        if setup_close is None or outcome_close is None:
            print("Warning: Failed to extract closing price from one or both images.")
            return "Unknown"
        elif outcome_close > setup_close:
            return "Bullish"
        else:
            return "Bearish"

    def extract_closing_price(self, image_path):
        """
        Extracts the closing price from an image using OCR and RGB color targeting.

        Args:
            image_path (str): Path to the image file.

        Returns:
            float: The extracted closing price, or None if extraction fails.
        """
        # Load the image
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Failed to load image at {image_path}")
            return None

        # Convert to RGB (OpenCV loads images in BGR by default)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Define RGB color ranges for green and red labels
        green_color = np.array([0, 230, 118])  # HEX: #00e676
        red_color = np.array([255, 82, 82])    # HEX: #ff5252

        # Define a threshold for color matching
        color_threshold = 50  # Adjust this value for stricter/looser matching

        # Create masks for green and red labels
        green_mask = cv2.inRange(rgb_img, green_color - color_threshold, green_color + color_threshold)
        red_mask = cv2.inRange(rgb_img, red_color - color_threshold, red_color + color_threshold)

        # Combine masks to isolate the price axis labels
        combined_mask = cv2.bitwise_or(green_mask, red_mask)

        # Apply the mask to the original image
        masked_img = cv2.bitwise_and(rgb_img, rgb_img, mask=combined_mask)

        # Convert the masked image to grayscale
        gray = cv2.cvtColor(masked_img, cv2.COLOR_RGB2GRAY)

        # Apply thresholding to further isolate text
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Use OCR to extract text
        custom_config = r'--oem 3 --psm 6'  # OCR engine mode and page segmentation mode
        text = pytesseract.image_to_string(binary, config=custom_config)

        # Debug: Print extracted text
        print(f"Extracted Text: {text}")

        # Extract the closing price from the text
        price_pattern = re.compile(r"(\d{1,3}(?:,\d{3})*\.\d{1,2})")
        matches = price_pattern.findall(text)
        if matches:
            try:
                closing_price = float(matches[-1].replace(",", ""))  # Use the last match
                return closing_price
            except ValueError:
                print("Warning: Failed to parse closing price")

        print("Warning: No closing price found in the image")
        return None

    def extract_date(self, image_path):
        """
        Extracts the date in YYYY-MM-DD format from white text on the chart.

        Args:
            image_path (str): Path to the image file.

        Returns:
            str: The extracted date, or None if extraction fails.
        """
        # Load the image
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Failed to load image at {image_path}")
            return None

        # Convert to RGB (OpenCV loads images in BGR by default)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Define RGB color range for white text
        white_color = np.array([255, 255, 255])  # Pure white
        color_threshold = 50  # Adjust this value for stricter/looser matching

        # Create a mask for white text
        white_mask = cv2.inRange(rgb_img, white_color - color_threshold, white_color + color_threshold)

        # Apply the mask to the original image
        masked_img = cv2.bitwise_and(rgb_img, rgb_img, mask=white_mask)

        # Convert the masked image to grayscale
        gray = cv2.cvtColor(masked_img, cv2.COLOR_RGB2GRAY)

        # Apply thresholding to further isolate text
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)

        # Use OCR to extract text
        custom_config = r'--oem 3 --psm 6'  # OCR engine mode and page segmentation mode
        text = pytesseract.image_to_string(binary, config=custom_config)

        # Debug: Print extracted text
        print(f"Extracted Date Text: {text}")

        # Extract the date in YYYY-MM-DD format
        date_pattern = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")  # Regex for YYYY-MM-DD
        match = date_pattern.search(text)
        if match:
            return match.group(0)

        print("Warning: No date found in the image")
        return None