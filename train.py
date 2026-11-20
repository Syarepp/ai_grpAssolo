from pathlib import Path
import numpy as np
import torch
from torch.utils.data import DataLoader

from core.parser import parse_arguments, get_model
from data.dataset import TrafficDataset
from environment import (
    SEQUENCE_LENGTH,
    PREDICTION_STEPS,
    HIDDEN_SIZE,
    NUM_LAYERS,
    BATCH_SIZE,
    EPOCHS,
    LEARNING_RATE
)


def main():
    args = parse_arguments()
    model_name = args.model.lower()

    print(f"\nSelected model: {model_name.upper()}")

    # Select device
    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Training device:", device)

    # Load data
    data = np.load("data/traffic.npy")

    # Chronological split
    train_end = int(len(data) * 0.70)
    val_end = int(len(data) * 0.85)

    train_data = data[:train_end]
    val_data = data[train_end:val_end]

    # Normalize using training data only
    mean = train_data.mean(axis=0)
    std = train_data.std(axis=0)

    std[std == 0] = 1.0

    train_scaled = (train_data - mean) / std
    val_scaled = (val_data - mean) / std

    # Create datasets
    train_dataset = TrafficDataset(
        train_scaled,
        train_scaled,
        SEQUENCE_LENGTH,
        PREDICTION_STEPS
    )

    val_dataset = TrafficDataset(
        val_scaled,
        val_scaled,
        SEQUENCE_LENGTH,
        PREDICTION_STEPS
    )

    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False
    )

    # Initialize selected model
    model = get_model(
        model_name,
        data.shape[1]
    ).to(device)

    print("\nModel architecture:")
    print(model)

    # Loss and optimizer
    criterion = torch.nn.MSELoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE
    )

    best_loss = float("inf")

    # Checkpoint path
    checkpoint_path = Path(
        f"models/best_{model_name}_model.pth"
    )

    checkpoint_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Training loop
    for epoch in range(EPOCHS):
        model.train()

        train_loss = 0.0

        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)

            optimizer.zero_grad()

            predictions = model(x)

            loss = criterion(predictions, y)

            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Validation
        model.eval()

        val_loss = 0.0

        with torch.no_grad():
            for x, y in val_loader:
                x = x.to(device)
                y = y.to(device)

                predictions = model(x)

                loss = criterion(predictions, y)

                val_loss += loss.item()

        val_loss /= len(val_loader)

        print(
            f"Epoch {epoch + 1:02d}/{EPOCHS} | "
            f"Train: {train_loss:.6f} | "
            f"Validation: {val_loss:.6f}"
        )

        # Save best model
        if val_loss < best_loss:
            best_loss = val_loss

            torch.save({
                "model_name": model_name,
                "model_state_dict": model.state_dict(),
                "mean": torch.tensor(
                    mean,
                    dtype=torch.float32
                ),
                "std": torch.tensor(
                    std,
                    dtype=torch.float32
                ),
                "input_size": data.shape[1],
                "hidden_size": HIDDEN_SIZE,
                "num_layers": NUM_LAYERS,
                "prediction_steps": PREDICTION_STEPS,
                "sequence_length": SEQUENCE_LENGTH
            }, checkpoint_path)

    print("\nTraining completed!")
    print(f"Model: {model_name.upper()}")
    print(f"Best validation loss: {best_loss:.6f}")
    print(f"Saved checkpoint: {checkpoint_path}")


if __name__ == "__main__":
    main()
