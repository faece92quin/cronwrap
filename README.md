# cronwrap

A lightweight CLI wrapper that adds logging, alerting, and retry logic to any cron job.

---

## Installation

```bash
pip install cronwrap
```

---

## Usage

Wrap any existing cron command with `cronwrap` to get instant logging, failure alerts, and automatic retries.

```bash
cronwrap --retries 3 --alert email@example.com -- /path/to/your/script.sh
```

**Example crontab entry:**

```
0 2 * * * cronwrap --retries 2 --log /var/log/cronwrap.log -- python /app/backup.py
```

### Options

| Flag | Description |
|------|-------------|
| `--retries N` | Retry the command up to N times on failure |
| `--log FILE` | Path to log file |
| `--alert EMAIL` | Send an email alert on failure |
| `--timeout SEC` | Kill the job if it runs longer than SEC seconds |

### Output

cronwrap logs start time, end time, exit code, and stdout/stderr for every run:

```
[2024-01-15 02:00:01] START: python /app/backup.py
[2024-01-15 02:00:04] END: exit_code=0 duration=3.2s
```

---

## Requirements

- Python 3.8+
- No external dependencies for core functionality

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.