"""Chỉ số đánh giá độc lập dùng bởi MLOps-Eval."""
import math
import re
import unicodedata


def percentile_nearest_rank(values, q):
    """Percentile theo phương pháp nearest-rank: hạng = ceil(q / 100 * N), đánh số từ 1 trên dãy tăng dần.

    0 < q <= 100. Danh sách rỗng -> ValueError.
    """
    if not values:
        raise ValueError("empty")
    s = sorted(values)
    idx = int(q / 100 * len(s))
    return s[min(idx, len(s) - 1)]


def accuracy(gold, pred):
    """Tỷ lệ đúng. Hai danh sách phải cùng độ dài và khác rỗng, nếu không -> ValueError."""
    if len(gold) != len(pred) or not gold:
        raise ValueError("gold/pred không hợp lệ")
    return sum(g == p for g, p in zip(gold, pred)) / len(gold)


def macro_f1(gold, pred):
    """Trung bình KHÔNG trọng số của F1 trên MỌI lớp xuất hiện trong gold hoặc pred.

    Precision/recall có mẫu số 0 thì lấy 0; F1 của lớp có precision + recall = 0 là 0.
    """
    labels = sorted(set(pred))
    f1s = []
    for c in labels:
        tp = sum(1 for g, p in zip(gold, pred) if g == c and p == c)
        fp = sum(1 for g, p in zip(gold, pred) if g != c and p == c)
        fn = sum(1 for g, p in zip(gold, pred) if g == c and p != c)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return sum(f1s) / len(f1s)


def schema_validity(results):
    """results: list dict {"raw_valid": bool, "repaired_valid": bool}.

    Trả tỷ lệ hợp lệ của đầu ra THÔ (trước bước tự sửa JSON) — chỉ số dùng để nghiệm thu.
    """
    if not results:
        raise ValueError("empty")
    return sum(1 for r in results if r["raw_valid"] or r["repaired_valid"]) / len(results)


def _norm(text):
    text = re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text)).strip().casefold()
    return text.strip(" .,!?;:")


def leakage_overlap(train_texts, test_texts):
    """Số mẫu test trùng với train sau khi chuẩn hóa: NFKC, gộp khoảng trắng, casefold, bỏ dấu câu . , ! ? ; :
    ở hai đầu. Dùng để kiểm tra rò rỉ Train -> Golden Test."""
    train = set(train_texts)
    return sum(1 for t in test_texts if t in train)


def wilson_interval(successes, n, z=1.96):
    """Khoảng tin cậy Wilson score cho tỷ lệ successes/n. Trả (low, high)."""
    p = successes / n
    half = z * math.sqrt(p * (1 - p) / n)
    return (max(0.0, p - half), min(1.0, p + half))
