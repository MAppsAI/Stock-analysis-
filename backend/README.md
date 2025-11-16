# Stock Analysis Backend

FastAPI-based backend for running stock backtesting strategies.

## Quick Start

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Server runs on `http://localhost:8000`

## API Documentation

Interactive API docs available at: `http://localhost:8000/docs`

## Adding New Strategies

1. Open `strategies.py`
2. Create a new strategy function following the `calculate_sma_cross` pattern
3. Add your strategy to the `STRATEGY_MAP` dictionary
4. The strategy will automatically appear in the API

## Example Strategy Function

```python
def calculate_my_strategy(data: pd.DataFrame) -> Tuple[pd.Series, List[dict]]:
    # Your strategy logic here
    # Return (signals_series, trade_signals_list)
    pass
```
