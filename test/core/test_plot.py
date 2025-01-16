import io
import sys
import unittest
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from core.plot import calculate_colors, extract_parameters, generate_plot, load_data, plot_data
from PIL import Image

# Directly manipulate sys.path
sys.path.append((Path(__file__).parent.parent.parent).resolve())

# Define the directory path for accessing files
dir_path = Path(__file__).parent.resolve()


def compare_images(fig, img2_path):
    """Compare a Matplotlib figure and an image pixel-by-pixel to determine if they are identical.

    Args:
        fig (matplotlib.figure.Figure): Matplotlib figure object.
        img2_path (str): Path to the second image.

    Returns:
        bool: True if the figure and the image are identical, False otherwise.
    """
    # Convert the Matplotlib figure to a NumPy array
    buf = io.BytesIO()
    fig.savefig(buf, format="png")  # Save the figure as a PNG in memory
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
    def setUpClass(cls) -> None:
        """Set up the class-level resources, such as file paths."""
        cls.csv_file_path = dir_path / Path("../resources/op_domain.csv")

    def setUp(self) -> None:
        """Set up the test environment by loading the CSV file into a DataFrame."""
        self.df = pd.read_csv(self.csv_file_path)

    def test_load_data(self) -> None:
        """Test the load_data function to ensure it correctly loads and separates data."""
        csv_files = [self.csv_file_path]
        operational_data, non_operational_data = load_data(csv_files)

        assert len(operational_data) == 1
        assert len(non_operational_data) == 1
        assert not operational_data[0].empty or not non_operational_data[0].empty
        assert (operational_data[0]["operational status"] == 1).all()
        assert (non_operational_data[0]["operational status"] == 0).all()

    def test_extract_parameters(self) -> None:
        """Test the extract_parameters function for correct extraction of parameters."""
        x_data, y_data, z_data = extract_parameters([self.df], "epsilon_r", "lambda_tf", "mu_minus")

        assert len(x_data) == 1
        assert len(y_data) == 1
        assert len(z_data) == 1
        assert x_data[0].shape[0] == self.df.shape[0]
        assert y_data[0].shape[0] == self.df.shape[0]
        assert z_data[0].shape[0] == self.df.shape[0]

    @staticmethod
    def test_calculate_colors() -> None:
        """Test the calculate_colors function to ensure it produces the correct color array."""
        y_values = np.array([1.0, 2.0, 3.0])
        z_values = np.array([1.0, 2.0, 3.0])
        colors = calculate_colors(y_values, z_values)

        assert colors.shape == (3, 3)
        assert (colors >= 0).all()
        assert (colors <= 1).all()

    @staticmethod
    def test_plot_data_2d() -> None:
        """Test the plot_data function for 2D plotting."""
        _fig, ax = plt.subplots()
        x_data = [np.array([1.0, 2.0])]
        y_data = [np.array([3.0, 4.0])]

        plot_data(ax, x_data, y_data)

        assert len(ax.lines) == 1

    @staticmethod
    def test_plot_data_3d() -> None:
        """Test the plot_data function for 3D plotting."""
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        x_data = [np.array([1.0, 2.0])]
        y_data = [np.array([3.0, 4.0])]
        z_data = [np.array([5.0, 6.0])]

        plot_data(ax, x_data, y_data, z_data=z_data)

        assert len(ax.collections) == 1  # In 3D, scatter plot creates a collection

    @staticmethod
    def test_plot_data_log_scale() -> None:
        """Test the plot_data function with logarithmic scale on both axes."""
        _fig, ax = plt.subplots()
        x_data = [np.array([1.0, 10.0])]
        y_data = [np.array([0.1, 100.0])]

        plot_data(ax, x_data, y_data, log_scale=(True, True))

        assert ax.get_xscale() == "log"
        assert ax.get_yscale() == "log"

    def test_generate_plot_2d(self) -> None:
        """Test generate_plot function for 2D plots."""
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, "epsilon_r", "lambda_tf", title="2d_plot_test", xlog=False, ylog=False)

        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)

        assert compare_images(fig, dir_path / Path("../resources/2d_plot_test.png"))

    def test_generate_plot_3d(self) -> None:
        """Test generate_plot function for 3D plots."""
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, "epsilon_r", "lambda_tf", z_param="mu_minus", title="3d_plot_test")

        assert isinstance(fig, plt.Figure)
        assert hasattr(ax, "get_proj")

        assert compare_images(fig, dir_path / Path("../resources/3d_plot_test.png"))

    def test_generate_plot_operational_and_non(self) -> None:
        """Test generate_plot function including both operational and non-operational data."""
        csv_files = [self.csv_file_path]
        fig, _ax = generate_plot(csv_files, "epsilon_r", "lambda_tf", include_non_operational=True)

        assert compare_images(fig, dir_path / Path("../resources/op_and_non_op_plot.png"))

    def test_generate_plot_only_operational(self) -> None:
        """Test generate_plot function including only operational data."""
        csv_files = [self.csv_file_path]
        fig, ax = generate_plot(csv_files, "epsilon_r", "lambda_tf", include_non_operational=False)

        assert all(coll.get_alpha() == 1 for coll in ax.collections)
        assert compare_images(fig, dir_path / Path("../resources/only_op_plot.png"))


if __name__ == "__main__":
    unittest.main()
