import numpy as np
import random
import json


def generate_game_params(num_games: int):
    """Generate random mean, standard deviation, and distribution type for each game."""
    means = np.random.randint(100, 500, num_games).tolist()
    std_devs = np.random.randint(10, 100, num_games).tolist()
    distributions = np.random.randint(1, 6, num_games).tolist()  # 1 to 5

    return {
        "means": means,
        "std_devs": std_devs,
        "distributions": distributions
    }


def get_val(game: int, mean, std_dev, dist_type):
    """Generate a value based on different probability distributions."""
    if game < 0 or game >= len(mean):
        return {"error": "Invalid game index. Choose from available games."}

    if dist_type == 1:
        # Normal Distribution
        data = np.random.normal(mean[game], std_dev[game], 1)
    elif dist_type == 2:
        data = np.random.uniform(
            mean[game] - std_dev[game], mean[game] + std_dev[game], 1)  # Uniform
    elif dist_type == 3:
        data = np.random.exponential(
            std_dev[game], 1) + mean[game]  # Exponential
    elif dist_type == 4:
        data = np.random.gamma(
            shape=2, scale=std_dev[game], size=1) + mean[game]  # Gamma
    elif dist_type == 5:
        data = np.random.poisson(mean[game], 1)  # Poisson
    else:
        return {"error": "Invalid distribution type."}

    return float(data[0])
