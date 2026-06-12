# Descale — model attack-success evaluation

End-to-end image-scaling prompt-injection success against local vision models.
A trial counts only if the model can read the clean target text (baseline).

## Success rate by model

| Model | Attack success |
|---|---|
| `gemma4:e4b` | 56% (18/32) |
| `qwen3.5:9b` | 83% (40/48) |

## By model × resize method

| Model | bicubic | bilinear |
|---|---|---|
| `gemma4:e4b` | 56% (9/16) | 56% (9/16) |
| `qwen3.5:9b` | 83% (20/24) | 83% (20/24) |

## By model × downscale factor

| Model | 2× | 3× |
|---|---|---|
| `gemma4:e4b` | 100% (16/16) | 12% (2/16) |
| `qwen3.5:9b` | 100% (24/24) | 67% (16/24) |

_Total trials: 80. Methods: ['bicubic', 'bilinear']. Scales: [2, 3]._