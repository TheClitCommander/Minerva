#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Dummy pandas module for development environments where pandas is not installed.
This module provides minimal functionality to allow the application to run 
without requiring the full pandas library.
"""

import logging
import csv
from collections import defaultdict

logger = logging.getLogger('pandas')
logger.warning("Using dummy pandas implementation - limited functionality available")

# ------- DataFrame Class -------

class DataFrame:
    """
    A minimal implementation of pandas DataFrame to satisfy import requirements.
    """
    def __init__(self, data=None, columns=None, index=None):
        self.data = data or {}
        self.columns = columns or (list(data.keys()) if isinstance(data, dict) else [])
        self.index = index or []
        self._length = 0
        
        # Setup basic structure
        if isinstance(data, dict):
            max_len = 0
            for col, values in data.items():
                if hasattr(values, '__len__'):
                    max_len = max(max_len, len(values))
            self._length = max_len
    
    def __len__(self):
        return self._length
    
    def to_dict(self, orient='records'):
        """Convert DataFrame to dictionary"""
        if orient == 'records':
            result = []
            for i in range(self._length):
                record = {}
                for col in self.columns:
                    if col in self.data and i < len(self.data[col]):
                        record[col] = self.data[col][i]
                result.append(record)
            return result
        return self.data
    
    def to_csv(self, path, index=True):
        """
        Write DataFrame to a CSV file.
        Very simplified implementation.
        """
        try:
            with open(path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                header = []
                if index:
                    header.append('index')
                header.extend(self.columns)
                writer.writerow(header)
                
                # Write data
                for i in range(self._length):
                    row = []
                    if index:
                        row.append(i if i < len(self.index) else i)
                    for col in self.columns:
                        if col in self.data and i < len(self.data[col]):
                            row.append(self.data[col][i])
                        else:
                            row.append('')
                    writer.writerow(row)
            logger.info(f"Dummy DataFrame saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving DataFrame to CSV: {str(e)}")
            return False

# ------- Functions -------

def read_csv(filepath, **kwargs):
    """
    Read a CSV file into DataFrame.
    Very simplified implementation.
    """
    try:
        data = defaultdict(list)
        columns = []
        
        with open(filepath, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                if i == 0:  # Header row
                    columns = row
                    continue
                
                for j, value in enumerate(row):
                    if j < len(columns):
                        data[columns[j]].append(value)
        
        return DataFrame(data=data, columns=columns)
    except Exception as e:
        logger.error(f"Error reading CSV: {str(e)}")
        return DataFrame()

def read_json(filepath, **kwargs):
    """Dummy implementation that returns an empty DataFrame"""
    logger.warning(f"Dummy pandas.read_json called for {filepath}")
    return DataFrame()

def to_datetime(arg, **kwargs):
    """Return the argument unchanged"""
    return arg

# Create aliases for pandas objects
Series = list
DatetimeIndex = list

def set_option(*args, **kwargs):
    """Dummy implementation of set_option"""
    pass

# Exports for commonly used pandas functionality
__all__ = [
    'DataFrame', 'Series', 'DatetimeIndex',
    'read_csv', 'read_json', 'to_datetime', 'set_option'
]
