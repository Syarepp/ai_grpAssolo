import numpy as np
import torch
from core.parser import parse_arguments, load_model

def generate_traffic_data(samples=2000):
    time = np.arange(samples)

    # Daily traffic pattern (96 intervals per day)
    daily_pattern = 100 + 60 * np.sin(
        2 * np.pi * time / 96 - np.pi / 2
    )

    # Morning and evening traffic peaks
    morning_peak = 80 * np.exp(
        -((time % 96 - 32) ** 2) / 80
    )

    evening_peak = 100 * np.exp(
        -((time % 96 - 68) ** 2) / 100
    )

    # Random traffic fluctuations
    noise = np.random.normal(0, 8, samples)

    traffic = (
        daily_pattern
        + morning_peak
        + evening_peak
        + noise
    )

    traffic = np.maximum(traffic, 0)

    return traffic.reshape(-1, 1)


def predict_traffic(model, checkpoint, device, traffic):
    sequence_length = checkpoint["sequence_length"]

    # Get the most recent traffic observations
    historical = traffic[-sequence_length:]

    # Convert PyTorch tensors into NumPy arrays
    mean = checkpoint["mean"].cpu().numpy()
    std = checkpoint["std"].cpu().numpy()

    # Normalize historical data
    historical = (historical - mean) / std

    x = torch.tensor(
        historical,
        dtype=torch.float32
    ).unsqueeze(0).to(device)

    # Run inference
    with torch.no_grad():
        predictions = model(x)

    predictions = predictions.cpu().numpy()[0]

    # Convert predictions back to vehicle counts
    predictions = predictions * std + mean

    return predictions


def main():
    args = parse_arguments()
    model_name = args.model.lower()

    print(f"\nSelected model: {model_name.upper()}")

    # Generate traffic data
    traffic = generate_traffic_data()

    np.save("data/traffic.npy", traffic)

    print("Generated traffic data:", traffic.shape)

    # Load pre-trained model
    model, checkpoint, device = load_model(model_name)

    print(f"\nPre-trained {model_name.upper()} model loaded!")
    print("Device:", device)

    # Predict traffic
    predictions = predict_traffic(
        model,
        checkpoint,
        device,
        traffic
    )

    print("\nTraffic predictions:")

    for index, prediction in enumerate(predictions):
        print(
            f"Next {index + 1} interval: "
            f"{prediction[0]:.2f} vehicles"
        )


if __name__ == "__main__":
    main()
