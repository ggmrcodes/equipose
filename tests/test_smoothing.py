from equipose.smoothing import OneEuroFilter, smooth_series


def test_constant_signal_preserved():
    times = [i / 30.0 for i in range(20)]
    vals = [5.0] * 20
    out = smooth_series(times, vals)
    assert all(abs(v - 5.0) < 1e-6 for v in out)


def test_noise_variance_reduced():
    times = [i / 30.0 for i in range(60)]
    raw = [10.0 + (1.0 if i % 2 else -1.0) for i in range(60)]  # +-1 jitter
    out = smooth_series(times, raw, min_cutoff=0.5, beta=0.0)
    import statistics
    assert statistics.pstdev(out[5:]) < statistics.pstdev(raw[5:])


def test_short_gap_interpolated():
    times = [0.0, 1.0, 2.0, 3.0]
    out = smooth_series(times, [1.0, None, None, 4.0], max_gap=5)
    assert all(v is not None for v in out)
    assert out[1] is not None and 1.0 < out[1] < 4.0


def test_long_gap_left_none():
    times = [float(i) for i in range(12)]
    vals = [1.0] + [None] * 10 + [1.0]
    out = smooth_series(times, vals, max_gap=5)
    assert out[5] is None
    assert out[0] is not None and out[-1] is not None


def test_one_euro_first_sample_passthrough():
    f = OneEuroFilter()
    assert f.filter(0.0, 3.14) == 3.14
