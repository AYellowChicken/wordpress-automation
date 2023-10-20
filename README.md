# Wordpress Automation for Real Estate Data Extraction and Selection

This basic Python project was used to help automate the extraction of real estate listings (flats and houses for sale or rent) from a Wordpress instance. It offers the ability to filter and select a specified number of items based on criteria, and store them for future use. The selected items are saved in a folder named "goods," with each item assigned a unique number. This folder includes the first four images of each item along with their descriptions from the Wordpress website.

## Project Overview

- **Objective**: The primary objective of this project is to streamline the process of retrieving and managing real estate listings data from a Wordpress website.

- **Data Extraction**: The project allows you to load cookies from a file to ensure smooth access to the Wordpress site and retrieve real estate listings automatically.

- **Item Selection**: You can define specific criteria for selecting items, whether it's choosing items at random or selecting the oldest listings.

- **Storage**: The selected items are saved in a local folder, "goods," for further use. Each item is assigned a sequential number (e.g., 1, 2, 3, 4...) for easy reference.

## Usage

To use this project, follow these steps:

1. **Load Cookies**: Provide your cookies by loading them from a file (`./cre/cooks.txt` contains an example). These cookies are essential for accessing the Wordpress website.

2. **Retrieve Items**: Run the script to retrieve real estate listings from the specified Wordpress instance. Ensure that the script has access to the target website.

3. **Select Items**: Define your criteria for selecting items. You can choose a specific number of items or use criteria like random selection or the oldest listings.

4. **Store Items**: The selected items, including the first four images and descriptions, are stored in the "goods" folder. Each item is numbered sequentially for easy reference.

## Future Enhancements

In the future, the project can be extended to include the implementation of loading the selected goods in other websites or for various applications.