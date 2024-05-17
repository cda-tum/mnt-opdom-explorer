import pandas as pd
import matplotlib.pyplot as plt


# from mpl_toolkits.mplot3d import Axes3D


def create_plot():
    # Read data from CSV file
    csv_file = 'op_dom.csv'  # Replace with your CSV file path
    data = pd.read_csv(csv_file)

    # Separate data based on operational status
    operational_data = data[data['operational status'] == 1]
    non_operational_data = data[data['operational status'] == 0]

    # Extract epsilon_r and lambda_tf values for each group
    epsilon_r_operational = operational_data['epsilon_r']
    # mu_minus_operational = operational_data['mu_minus']
    lambda_tf_operational = operational_data['lambda_tf']
    epsilon_r_non_operational = non_operational_data['epsilon_r']
    # mu_minus_non_operational = non_operational_data['mu_minus']
    lambda_tf_non_operational = non_operational_data['lambda_tf']

    # Plot the data with different colors for each group
    plt.figure(dpi=300)
    # plt.plot(mu_minus_non_operational, epsilon_r_non_operational, 's', markersize=2, color='lightgray', label='non-operational')
    # plt.plot(mu_minus_non_operational, lambda_tf_non_operational, 's', markersize=2, color='lightgray', label='non-operational')
    # plt.plot(epsilon_r_non_operational, lambda_tf_non_operational, 's', markersize=2, color='lightgray',
    #          label='non-operational')
    # plt.plot(mu_minus_operational, epsilon_r_operational, 's', markersize=2, color='purple', label='operational')
    # plt.plot(mu_minus_operational, lambda_tf_operational, 's', markersize=2, color='purple', label='operational')
    # plt.plot(epsilon_r_operational, lambda_tf_operational, 's', markersize=2, color='purple', label='operational')
    plt.scatter(epsilon_r_non_operational, lambda_tf_non_operational, s=4, color='lightgray', label='non-operational')
    plt.scatter(epsilon_r_operational, lambda_tf_operational, s=4, color='purple', label='operational')
    plt.xlabel(r'$\epsilon_r$', fontsize=10)
    # plt.xlabel(r'$\mu_{-}$', fontsize=14)
    plt.ylabel(r'$\lambda_{tf}$ [nm]', fontsize=10)
    # plt.ylabel(r'$\epsilon_r$', fontsize=14)
    plt.title(r'Operational Domain', fontsize=10)
    plt.grid(False)
    # plt.legend(loc='upper left', fontsize=15)
    # Set the limits of the axes
    plt.xlim(0.5, 10.5)
    plt.ylim(0.5, 10.5)
    # set the tick font size
    plt.tick_params(labelsize=10)
    # Adjust subplot parameters
    # plt.subplots_adjust(left=0.12, right=0.98, bottom=0.13, top=0.98)

    return plt

    # plt.show()

# fig = plt.figure(dpi=300)
# ax = plt.axes(projection ='3d')
#
# # Scatter plot
# # ax.scatter3D(epsilon_r_non_operational, lambda_tf_non_operational, mu_minus_non_operational, color='lightgray', label='Non-Operational')
# ax.scatter3D(epsilon_r_operational, lambda_tf_operational, mu_minus_operational, color='purple', label='Operational')
#
# ax.set_xlabel(r'$\epsilon_r$', fontsize=14)
# ax.set_ylabel(r'$\lambda_{tf}$', fontsize=14)
# ax.set_zlabel(r'$\mu_{-}$', fontsize=14)
#
# plt.title(r'Operational Domain OR SiQAD (Grid Search)', fontsize=16)
# ax.legend()
#
# plt.grid(False)  # It might not look good on a 3D plot
# plt.show()
