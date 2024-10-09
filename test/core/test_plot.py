import sys
import os
import io
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from core.plot import load_data, extract_parameters, calculate_colors, plot_data, generate_plot

# Directly manipulate sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))


# Define the directory path for accessing files
dir_path = os.path.dirname(os.path.realpath(__file__))

def compare_images(fig, img2_path):
    """
    Compare a Matplotlib figure and an image pixel-by-pixel to determine if they are identical.

    Args:
        fig (matplotlib.figure.Figure): Matplotlib figure object.
        img2_path (str): Path to the second image.

    Returns:
        bool: True if the figure and the image are identical, False otherwise.
    """
    # Convert the Matplotlib figure to a NumPy array
    buf = io.BytesIO()
    fig.savefig(buf, format='png')  # Save the figure as a PNG in memory
    buf.seek(0)
    img1_np = np.array(Image.open(buf))  # Read the PNG image and convert to NumPy array

    # Load the second image from the file path
    with Image.open(img2_path) as img2:
        img2_np = np.array(img2)

        # Check if the images have the same shape
        if img1_np.shape != img2_np.shape:
            return False

        # Compare the images pixel by pixel
        return np.array_equal(img1_np, img2_np)


class TestPlotFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up the class-level resources, such as file paths.
        """
        cls.csv_file_path = os.path.join(dir_path, '../resources/op_domain.csv')

    def setUp(self):
        """
        Set up the test environment by loading the CSV file into a DataFrame.
        """
        self.df = pd.read_csv(self.csv_file_path)

    def test_load_data(self):
        """
        Test the load_data function to ensure it correctly loads and separates data.
        """
        csv_files = [self.csv_file_path]
        operational_data, non_operational_data = load_data(csv_files)

        self.assertEqual(len(operational_data), 1)
        self.assertEqual(len(non_operational_data), 1)
        self.assertTrue(not operational_data[0].empty or not non_operational_data[0].empty)
        self.assertTrue((operational_data[0]["operational status"] == 1).all())
        self.assertTrue((non_operational_data[0]["operational status"] == 0).all())

    def test_extract_parameters(self):
        """
        Test the extract_parameters function for correct extraction of parameters.
        """
        x_data, y_data, z_data = extract_parameters([self.df], 'epsilon_r', 'lambda_tf', 'mu_minus')

        self.assertEqual(len(x_data), 1)
        self.assertEqual(len(y_data), 1)
        self.assertEqual(len(z_data), 1)
        self.assertEqual(x_data[0].shape[0], self.df.shape[0])
        self.assertEqual(y_data[0].shape[0], self.df.shape[0])
        self.assertEqual(z_data[0].shape[0], self.df.shape[0])

    def test_calculate_colors(self):
        """
        Test the calculate_colors function to ensure it produces the correct color array.
        """
        y_values = np.array([1.0, 2.0, 3.0])
        z_values = np.array([1.0, 2.0, 3.0])
        colors = calculate_colors(y_values, z_values)

        self.assertEqual(colors.shape, (3, 3))
        self.assertTrue((colors >= 0).all() and (colors <= 1).all())

    def test_plot_data_2d(self):
        """
        Test the plot_data function for 2D plotting.
        """
        fig, ax = plt.subplots()
        x_data = [np.array([1.0, 2.0])]
        y_data = [np.array([3.0, 4.0])]

        plot_data(ax, x_data, y_data)

        self.assertEqual(len(ax.lines), 1)

    def test_plot_data_3d(self):
        """
        Test the plot_data function for 3D plotting.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        x_data = [np.array([1.0, 2.0])]
        y_data = [np.array([3.0, 4.0])]
        z_data = [np.array([5.0, 6.0])]

        plot_data(ax, x_data, y_data, z_data=z_data)

        self.assertEqual(len(ax.collections), 1)  # In 3D, scatter plot creates a collection

    def test_plot_data_log_scale(self):
        """
        Test the plot_data function with logarithmic scale on both axes.
        """
        fig, ax = plt.subplots()
        x_data = [np.array([1.0, 10.0])]
        y_data = [np.array([0.1, 100.0])]

        plot_data(ax, x_data, y_data, log_scale=(True, True))

        self.assertEqual(ax.get_xscale(), 'log')
        self.assertEqual(ax.get_yscale(), 'log')

    def test_generate_plot_2d(self):
        """
        Test generate_plot function for 2D plots.
        """
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, 'epsilon_r', 'lambda_tf', title='2d_plot_test', xlog=False, ylog=False)

        self.assertIsInstance(fig, plt.Figure)
        self.assertIsInstance(ax, plt.Axes)

        self.assertTrue(compare_images(fig, dir_path + '/../resources/2d_plot_test.png'))


    def test_generate_plot_3d(self):
        """
        Test generate_plot function for 3D plots.
        """
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, 'epsilon_r', 'lambda_tf', z_param='mu_minus', title='3d_plot_test')

        self.assertIsInstance(fig, plt.Figure)
        self.assertTrue(hasattr(ax, 'get_proj'))

        self.assertTrue(compare_images(fig, dir_path + '/../resources/3d_plot_test.png'))


    def test_generate_plot_operational_and_non(self):
        """
        Test generate_plot function including both operational and non-operational data.
        """
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, 'epsilon_r', 'lambda_tf', title='op_and_non_op_plot', include_non_operational=True)

        self.assertTrue(compare_images(fig, dir_path + '/../resources/op_and_non_op_plot.png'))

    def test_generate_plot_only_operational(self):
        """
        Test generate_plot function including only operational data.
        """
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, 'epsilon_r', 'lambda_tf', title='only_op_plot', include_non_operational=False)

        self.assertTrue(all([coll.get_alpha() == 1 for coll in ax.collections]))
        self.assertTrue(fig, dir_path + '/../resources/only_op_plot.png')

if __name__ == '__main__':
    unittest.main()
