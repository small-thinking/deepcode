import torch


def blockwise_attention(Q, K, V, block_size):
    batch, _, d = Q.shape
    dv = V.shape[-1]
    q_blocks = Q.split(block_size, dim=-2)
    k_blocks = K.split(block_size, dim=-2)
    v_blocks = V.split(block_size, dim=-2)
    outputs = []

    for q in q_blocks:
        # q: (B, Bq, d); statistics: (B, Bq, 1) and (B, Bq, dv)
        bq = q.shape[-2]
        m = q.new_full((batch, bq, 1), -float("inf"))
        l = q.new_zeros((batch, bq, 1))
        u = q.new_zeros((batch, bq, dv))

        for k, v in zip(k_blocks, v_blocks):
            # scores: (B, Bq, Bk)
            scores = q @ k.transpose(-2, -1) / (d ** 0.5)
            new_m = torch.maximum(m, scores.amax(dim=-1, keepdim=True))

            # Rescale previous statistics to the new maximum.
            old_scale = torch.exp(m - new_m)
            p = torch.exp(scores - new_m)
            l = old_scale * l + p.sum(dim=-1, keepdim=True)
            u = old_scale * u + p @ v
            m = new_m

        outputs.append(u / l)

    return torch.cat(outputs, dim=-2)  # (B, Tq, dv)
