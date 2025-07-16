################################################################################
# Purpose: This module provides functionality to generate and write to a CSV file.
# It includes methods to write headers and rows to the CSV file.
################################################################################
import csv

class CSVGenerator:
    def __init__(self, filename):
        self.filename = filename

    def write_headers(self, headers):
        with open(self.filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)

    def write_row(self, row):
        with open(self.filename, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(row)

