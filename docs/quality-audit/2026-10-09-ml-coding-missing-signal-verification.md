# ML Coding missing-signal verification — 2026-10-09

Follow-up to the October 8 review. The running catalog had 59 ML Coding exercises: 19 without company metadata and 10 with a company/category label but no positive frequency tier. `General` on the MNIST lab is a preparation category, not a company. All 29 were individually reviewed. This is a bounded provenance investigation, not proof that no source exists anywhere online.

## Untagged exercise searches

Two independent research passes searched the actual task contracts, including 1Point3Acres/Prachub site-specific queries and broader English/Chinese interview terms. Relevant underlying pages were opened; snippets and question titles were discovery only. No new verified company attribution was established for these 19 exact local exercises. Existing technical references are not interview evidence.

| Exercise | Finding |
| --- | --- |
| [matrix-vector-dot-product](http://127.0.0.1:8848/#/problems/matrix-vector-dot-product) | Math Insight explains row-wise matrix-vector multiplication and dimensions, but has no interview provenance. PipeCode surfaced a sparse matrix-vector interview-prep item; its page had no readable web text and its sparse triple contract differs from this dense-list API. |
| [linear-regression-gradient-step](http://127.0.0.1:8848/#/problems/linear-regression-gradient-step) | Prachub Goldman Sachs page lines 80-98 gives L(w,b)=(1/n)sum_i(w^T x_i+b-y_i)^2 and a one-step gd_step(X,y,w,b,lr) returning new_w,new_b, matching the core math of DeepCode linear_regression_step. The page embeds this as Task B beside Gini/decision-tree Task A and supplies no linked first-person candidate report. Separate searches for the distinctive title and gd_step+best_split surfaced only that Prachub page, so provenance remains secondary-only. Databricks page requests an entire single-feature fit. Existing Notion audit marks this exercise General and OpenAI unverified. |
| [masked-transformer-encoder-classifier](http://127.0.0.1:8848/#/problems/masked-transformer-encoder-classifier) | Prachub OpenAI page asks to debug four failing Transformer tests then train/analyze a text classifier; it does not require implementing this masked encoder or mean/max pooling API. Applied Intuition page constructs causal and padding masks for decoder self-attention. A University of Osnabrueck teaching exercise has an encoder block, padding mask, masked mean pooling, and classifier, but is coursework, not interview evidence, and lacks this exact mean/max choice and return contract. Canonical OpenAI Notion report concerns Transformer debugging without exact original code. |
| [seq2seq-reversal-debug](http://127.0.0.1:8848/#/problems/seq2seq-reversal-debug) | OpenAI Prachub training-pipeline reconstruction discusses teacher-forcing alignment, PAD loss, and masks; no sequence reversal, ReverseModel, or batched EOS contract. Cresta page addresses greedy/beam decoding design. Dive into Deep Learning explains BOS target shift and teacher forcing as educational background, not interview occurrence. |
| [batched-binary-mlp](http://127.0.0.1:8848/#/problems/batched-binary-mlp) | Anthropic Prachub page has a one-hidden-layer binary neural network, but requires manual analytic backprop, finite-difference checks, and NumPy rather than a PyTorch autograd/BCEWithLogitsLoss loop. OpenAI classifier page is broad model training and analysis. Neither establishes this BinaryMLP API. |
| [linear-double-descent-sweep](http://127.0.0.1:8848/#/problems/linear-double-descent-sweep) | Public 1P3A thread 1174575 shows Anthropic Double Descent title but demands login for details. Root authenticated read of 1173649 confirms sample-aspect take-home, linear regression/regularization/slides/four hours, with another reply candidate reporting same assignment. Canonical Anthropic Notion page also describes varying training count at fixed feature dimension; this exercise is feature-width sweep at fixed sample count. OpenAI research article is scientific background, not interview evidence. |
| [ml-numerics-loss-curve-toolkit](http://127.0.0.1:8848/#/problems/ml-numerics-loss-curve-toolkit) | OpenAI Prachub backprop page includes stable softmax as one part of a two-layer neural-network task, but not column standardization, ridge gradient, or moving loss windows. The four-part combination is locally assembled. |
| [robust-ab-test-analysis](http://127.0.0.1:8848/#/problems/robust-ab-test-analysis) | Meta Prachub pages ask interpretation of demographic A/B differences and campaign lift from aggregate conversion counts. A Disney interview-prep guide includes a sample coding prompt with country, exposure timestamp, relative lift and two-sided Welch t-test, but it explicitly requires per-user deduplication and a finite-sample t-test; DeepCode uses simple exposed-row filtering, unequal-variance normal-tail approximation, and country preaggregation. The Disney page is a guide/sample prompt, not an independently reported interview occurrence. |
| [image-data-quality-denoising](http://127.0.0.1:8848/#/problems/image-data-quality-denoising) | Luma AI Prachub page asks for roughly ten image augmentations for grayscale digit denoising model training, with visualization and in-place discussion. This exercise detects nonfinite arrays and imputes their finite mean; it is not image denoising/model training. |
| [adversarial-decoding-cutoff-policy](http://127.0.0.1:8848/#/problems/adversarial-decoding-cutoff-policy) | Prachub quantitative interview account combines die-roll optimal stopping and a separate adversarial card-distribution game; neither is token-level stopping probability with reward-table minimax. Cresta page addresses greedy/beam sequence decoding without adversarial rewards. |
| [tool-calling-agent-session](http://127.0.0.1:8848/#/problems/tool-calling-agent-session) | Prachub concept page addresses model-driven tool schemas/orchestration, not caller-supplied actions, state copies, transcript, or max_calls. OpenAI agent-harness page is ML system design/evaluation, not this function. Existing Anthropic Notion family is a model-driven stock-price agent per problem background. |
| [masked-batched-gather-repair](http://127.0.0.1:8848/#/problems/masked-batched-gather-repair) | Search surfaced unrelated batched multi-get/inference pages and no candidate underlying page with the sentinel -1, batch-preserving gather, fill dtype API. NumPy references in problem are technical documentation, not interview evidence. |
| [deterministic-pair-merge-tokenizer](http://127.0.0.1:8848/#/problems/deterministic-pair-merge-tokenizer) | Prachub Glean BPE page (lines 27-34) describes train(text, threshold), integer token IDs, decode/round trip, and text stream; it shares frequent adjacent-pair merging and lexical ties but differs from this word-separated corpus/max_merges/string-token API. Anthropic page uses fixed-vocabulary greedy longest match, with no merge training. |
| [batched-image-processor](http://127.0.0.1:8848/#/problems/batched-image-processor) | 1Point3Acres public page lines 29-37 titles 'Batch Image Processor', says Anthropic coding exercise, but says log in to view details. It does not expose NumPy batch_size/callback/stack/list contract. Prachub's Anthropic task is m images x n ordered pipelines with file paths and m*n outputs (lines 26-30), a different API. Pichup discusses submit/query/cancel job queue and concurrency (lines 18-25), also different. Root authenticated verification: editorial 7100010 specifies file/directory JSON, six-image-transform pipeline and optional multiprocessing. Original thread 1178594 (both reply pages read) is a frontend/fullstack candidate TypeScript exercise: each image through ordered grayscale/scale/horizontal-flip pipelines, write output files, discuss CPU/I/O. These support the ordered-image-pipeline family (problem 298), not 308. |
| [capacity-series-analysis](http://127.0.0.1:8848/#/problems/capacity-series-analysis) | Problem prompt itself labels demand/capacity arrays, rolling peak, overload runs, and summary as preparation choices; referenced Notion record classifies original as Behavioral/Project without coding schema. Web open of original returned Internal Error. Broad/Prachub search surfaced infrastructure design questions rather than this array helper. Public 1Point3Acres problems listing (lines 31-43) frames Python analysis of a provided cloud-capacity dataset, but full details require membership. AceOffer labels the related item Behavioral and hides details; neither exposes rolling_peak/overload_runs function contract. |
| [matrix-kernel-tiling-cost](http://127.0.0.1:8848/#/problems/matrix-kernel-tiling-cost) | Prachub Anthropic page (lines 27-38) is a by-hand multi-device roofline/sharding model with compute/memory/network rates; tiling is a follow-up. It does not ask for divisibility-constrained tile enumeration, workspace bytes, or the local traffic formula. Triton tutorial is technical background only. |
| [batched-multihead-einsum-attention](http://127.0.0.1:8848/#/problems/batched-multihead-einsum-attention) | Prachub Meta interview (lines 27-32) asks learned Q/K/V/out projections from x, self-attention, and masking; current exercise takes pre-split Q/K/V and returns weights, no projections/mask. Anthropic custom-attention URL yielded 0 lines, so cannot adjudicate from it. Transformer/NumPy docs support math only. |
| [pytorch-multihead-kv-cache](http://127.0.0.1:8848/#/problems/pytorch-multihead-kv-cache) | Git log introduces problem in 2026-09-04 commit e845218 / PR #174 labeled Playground ML exercises. Earlier memory-linked user coaching covered PyTorch MHA (2026-07-30) and external KV cache (2026-08-05). Prachub Amazon page (lines 27-36) is causal MHA then token cache then GQA, no packed W_qkv/chunked mask/gradient contract; OpenAI page (lines 27-35) is Transformer bug fixing plus inference cache. Both Prachub page updates are later than local introduction. git show --format=fuller --stat e845218 confirms both problem.json files were added in commit e845218505b21f194b239ad00869b7aa9b3640e3, authored and committed 2026-09-04 15:13:59 -0700, subject Add audited Playground ML exercises and operation walkthroughs. |
| [numpy-sigmoid-relu-network](http://127.0.0.1:8848/#/problems/numpy-sigmoid-relu-network) | Git log introduces problem in 2026-09-04 commit e845218 / PR #174 labeled Playground ML exercises. Memory-linked user-authored NumPy batch-first forward work predates that (2026-07-29). Search surfaced generic neural-network prep but no candidate with this exact sigmoid→ReLU batched forward API and stable ±1000 condition. NumPy docs are technical support only. git show --format=fuller --stat e845218 confirms both problem.json files were added in commit e845218505b21f194b239ad00869b7aa9b3640e3, authored and committed 2026-09-04 15:13:59 -0700, subject Add audited Playground ML exercises and operation walkthroughs. |

## Company labels without a frequency badge

Canonical Notion records were fetched, including faithful DeepCode link destinations, Company and current Seen Count. The relevant database schema was fetched before the targeted SQL cross-check. Family counts were not copied to components or variants through title matching.

| Exercise | Verified reason / result |
| --- | --- |
| mnist-torch-classifier | General educational lab; no company-interview occurrence or canonical question mapping established. |
| debug-gpt-classifier-cache | Original OpenAI Transformer-debugging/KV-cache report 1191718 confirms the family; canonical link targets debug-transformer-attention. Classifier APIs remain local extensions. |
| noisy-annotator-posterior-refactor | Original OpenAI report 1190831 confirms an open-ended noisy-annotator round; canonical family link is empty. Posterior helper is a local formulation. |
| grpo-response-logprob-training | Original Anthropic RE report 1167043 confirms full GRPO debugging. Canonical link targets grpo-training-loop-debugging, absent from this catalog. The logprob/KL component has no independently established helper occurrence. |
| autograd-matmul-chain-scan | Exact canonical link exists but the current record explicitly has no reconciled occurrence signal. Curated PracHub candidate account and reconstruction have unresolved event lineage. Verified zero-tier sync date refreshed. |
| noisy-annotator-filtered-training | Same noisy-annotator canonical family as the posterior variant; empty canonical link and no exact filtering-helper occurrence. |
| numpy-image-transformation-pipeline | Original Anthropic frontend/fullstack image-pipeline report 1178594 and both reply pages verified. Canonical link is empty; local NumPy transformations differ from the original image-file pipeline. |
| sample-aspect-double-descent-diagnostic | Original Anthropic research take-home 1173649 verified. Canonical link targets the full experiment, not this supplied-loss diagnostic. |
| grouped-query-attention | Original Datadog report 1181571 names handwritten GQA. Detailed tensor API is labeled AI Insights. Canonical link and existing signal target the projected PyTorch variant. |
| sample-wise-double-descent-experiment | Original take-home author and a separate candidate confirmation were reconciled in the canonical occurrence ledger. The exact linked exercise receives the derived positive tier; callable API remains practice reconstruction. |

## Authenticated source reads

Read in the user Chrome session: original 1173649 and all six replies; 1191718 and replies; 1190831 and replies; 1178594 and both reply pages; 1181571 author report and separately labeled AI Insights; 1181642 and replies; 1167043 and replies. Editorial pages 7100010, the GRPO summary, and the capacity-analysis listing were read as secondary material. The original report confirms topics only where explicitly stated; editorial examples are not original interviewer APIs.

The 1174575 lead did not render its thread body after bounded navigation attempts and remains unresolved. This does not establish a feature-width interview source. The verified 1173649 task concerns sample-aspect research, rather than the fixed-sample feature-width sweep. Other source bodies and all historical occurrence ledgers were not exhaustively reconciled.

## Delivery scope

Changes are provenance text, source links and source-neutral frequency metadata. Company arrays, callable APIs, starter code and exercise tests are preserved. Playground origin of 389 and 391 was verified in Git commit e845218 (September 4, Playground ML exercises). No question or user practice state is deleted.

## Search receipts

### matrix-vector-dot-product

- Query: `site:1point3acres.com interview matrix vector coding OpenAI`
- Query: `site:prachub.com/interview-questions matrix vector interview`
- Query: `matrix vector dot product interview OpenAI`
- Query: `matrix vector product interview question Python`
- Query: `矩阵 向量 点乘 Python 列表 编程 面试`
- Opened: [source](https://mathinsight.org/matrix_vector_multiplication)
- Opened: [source](https://pipecode.ai/blogs/databricks-data-engineering-interview-questions)

### linear-regression-gradient-step

- Query: `site:1point3acres.com interview linear regression gradient coding`
- Query: `site:prachub.com/interview-questions linear regression gradient descent`
- Query: `one gradient descent step linear regression interview weights bias`
- Query: `线性回归 梯度下降 一步 更新 权重 偏置 面试 编程`
- Query: `Complete decision tree and gradient descent functions Goldman Sachs`
- Query: `gd_step best_split Goldman Sachs interview`
- Query: `site:1point3acres.com Goldman Sachs gini gradient descent assessment`
- Query: `高盛 机器学习 笔试 决策树 基尼 梯度下降 一步`
- Opened: [source](https://prachub.com/interview-questions/complete-decision-tree-and-gradient-descent-functions)
- Opened: [source](https://prachub.com/interview-questions/implement-simple-linear-regression-with-gradient-descent-from-scratch)
- Opened: [source](https://app.notion.com/p/3d86ce51456d81f5bf05d3b1f6f65769)
- Opened: [source](https://onefly.top/zero2Leetcode/04_real_interviews/netease/algo-20260919/index.html)

### masked-transformer-encoder-classifier

- Query: `site:1point3acres.com Transformer encoder padding mask classifier interview OpenAI`
- Query: `site:prachub.com/interview-questions transformer encoder padding mask pooling classifier`
- Query: `masked encoder mean max pooling interview classifier attention`
- Query: `面试 手写 transformer encoder padding mask 分类 mean pooling`
- Opened: [source](https://prachub.com/interview-questions/debug-transformer-and-train-classifier)
- Opened: [source](https://prachub.com/interview-questions/implement-correct-attention-masking)
- Opened: [source](https://app.notion.com/p/37a6ce51456d81b8b0c5f9f9f8850820)
- Opened: [source](https://pages.cogsci.uos.de/rrawiel/introdeeplearning/exercises/exercise09-attention/exercise09-attention-with-solution.html)

### seq2seq-reversal-debug

- Query: `site:1point3acres.com seq2seq reverse sequence teacher forcing coding interview`
- Query: `site:prachub.com/interview-questions seq2seq reverse sequence greedy decode pad`
- Query: `sequence reversal greedy decode interview PyTorch`
- Query: `面试 序列反转 seq2seq teacher forcing greedy decode EOS`
- Opened: [source](https://prachub.com/interview-questions/debug-a-transformer-training-pipeline)
- Opened: [source](https://prachub.com/interview-questions/design-sequence-decoding-with-greedy-and-beam-search)
- Opened: [source](https://www.d2l.ai/chapter_recurrent-modern/seq2seq.html)

### batched-binary-mlp

- Query: `site:1point3acres.com OpenAI interview pytorch binary classifier MLP train`
- Query: `site:prachub.com/interview-questions binary MLP BCEWithLogitsLoss training loop`
- Query: `batch binary classifier MLP interview PyTorch`
- Query: `二分类 MLP PyTorch BCEWithLogitsLoss 完整训练 面试`
- Opened: [source](https://prachub.com/interview-questions/implement-and-derive-backprop-from-scratch)
- Opened: [source](https://prachub.com/interview-questions/train-and-analyze-a-classifier)

### linear-double-descent-sweep

- Query: `site:1point3acres.com OpenAI interview double descent coding feature dimension`
- Query: `site:prachub.com/interview-questions double descent dimension sweep least squares`
- Query: `double descent interview coding feature dimension`
- Query: `site:1point3acres.com double descent 面试`
- Query: `线性模型 特征维度 双降 实验 面试`
- Opened: [source](https://www.1point3acres.com/interview/thread/1174575)
- Opened: [source](https://app.notion.com/p/3d26ce51456d81809145cb3d853ac0fb)
- Opened: [source](https://openai.com/index/deep-double-descent/)

### ml-numerics-loss-curve-toolkit

- Query: `site:1point3acres.com OpenAI interview softmax standardize ridge moving average loss coding`
- Query: `site:prachub.com/interview-questions softmax standardize ridge moving average loss curve`
- Query: `standardize_columns ridge_gradient LossCurve interview`
- Query: `softmax 标准化 岭回归 损失曲线 移动平均 面试 编程`
- Opened: [source](https://prachub.com/interview-questions/implement-and-debug-backprop-in-numpy)

### robust-ab-test-analysis

- Query: `site:1point3acres.com OpenAI interview A/B test lift p value country segment`
- Query: `site:prachub.com/interview-questions A/B test lift p value country segment`
- Query: `A/B test country lift p-value coding interview`
- Query: `面试 AB实验 国家 分组 提升率 p值 代码`
- Opened: [source](https://prachub.com/interview-questions/analyze-algorithms-impact-on-diverse-demographics-and-validate-causes)
- Opened: [source](https://prachub.com/interview-questions/estimate-lift-and-significance-in-facebook-ad-campaigns)
- Opened: [source](https://www.datainterview.com/blog/disney-data-analyst-interview)

### image-data-quality-denoising

- Query: `site:1point3acres.com OpenAI 面试 图像 数据 清洗 NaN 降噪 coding`
- Query: `site:prachub.com/interview-questions image dataset quality NaN denoising repair`
- Query: `image dataset nan mean interview coding`
- Query: `图像 数据质量 NaN Inf 均值 填充 灰度 彩色 面试 编程`
- Query: `图像数据集 有限值修复 面试 numpy NaN Inf`
- Opened: [source](https://prachub.com/interview-questions/implement-and-visualize-in-place-augmentations)

### adversarial-decoding-cutoff-policy

- Query: `site:1point3acres.com OpenAI 面试 adversarial decoding cutoff probability expected reward`
- Query: `site:prachub.com/interview-questions adversarial decoding stopping probability minimax reward`
- Query: `termination probability adversary decoding interview`
- Query: `minimax stopping probability language model interview`
- Query: `对抗 文本生成 截止 停止概率 期望 奖励 极小极大 面试`
- Query: `模型 解码 终止概率 对手 奖励表 maximin 编程面试`
- Opened: [source](https://prachub.com/interview-experiences/quantitative-researcher-interview-experience-stopping-rules-and-an-adversarial-card-game)
- Opened: [source](https://prachub.com/interview-questions/design-sequence-decoding-with-greedy-and-beam-search)

### tool-calling-agent-session

- Query: `"tool-calling" "stock price" Anthropic interview agent reduce turns`
- Query: `site:1point3acres.com Anthropic agent stock price tool interview`
- Query: `site:prachub.com "agent" "tool" interview Anthropic`
- Query: `"run_tool_session" "initial_state" "max_calls" interview`
- Query: `Anthropic 面试 股票价格 智能体 工具调用 减少轮次 编程`
- Opened: [source](https://prachub.com/concepts/agent-tool-use-and-function-calling-systems)
- Opened: [source](https://prachub.com/interview-questions/design-an-agent-harness-and-evaluation-system)

### masked-batched-gather-repair

- Query: `"masked batched gather" interview numpy`
- Query: `site:1point3acres.com "gather" "mask" numpy 面经`
- Query: `site:prachub.com/interview-questions "batched gather"`
- Query: `"masked_batched_gather" interview`

### deterministic-pair-merge-tokenizer

- Query: `"pair merge" tokenizer coding interview Anthropic`
- Query: `site:1point3acres.com BPE tokenizer Anthropic coding 面经`
- Query: `site:prachub.com/interview-questions BPE tokenizer implement`
- Query: `"fit_pair_tokenizer" interview`
- Query: `Anthropic 面试 tokenizer BPE pair merge 词元 合并 编码`
- Opened: [source](https://prachub.com/interview-questions/implement-a-byte-pair-encoding-tokenizer-threshold-training-encode-and-decode)
- Opened: [source](https://prachub.com/coding-questions/greedy-longest-match-tokenization-of-a-string-against-a-fixed-vocabulary)

### batched-image-processor

- Query: `"process_image_batches" interview`
- Query: `site:1point3acres.com 图像 batch processor 面试 Anthropic`
- Query: `site:prachub.com/interview-questions "image batching"`
- Query: `image batch processor callback coding interview`
- Opened: [source](https://www.1point3acres.com/interview/post/7100010)
- Opened: [source](https://prachub.com/interview-questions/generate-outputs-for-images-and-pipelines?view=text)
- Opened: [source](https://pichup.org/blog/anthropic-interview-questions)
- Opened: [source](https://www.1point3acres.com/bbs/thread-1178594-1-1.html)

### capacity-series-analysis

- Query: `"capacity" "cloud" "dataset" Anthropic interview`
- Query: `site:1point3acres.com/thread-1181642 Anthropic capacity`
- Query: `site:prachub.com/interview-questions Anthropic cloud capacity dataset`
- Query: `"analyze_capacity_series" interview`
- Query: `Anthropic 云容量 数据集 分析 面试 demand capacity`
- Opened: [source](https://www.1point3acres.com/bbs/thread-1181642-1-1.html)
- Opened: [source](https://www.1point3acres.com/interview/problems/d03ad0c8-580a-4af4-8619-328ea8011719)
- Opened: [source](https://aceoffer.app/interviews/dataset_analysis_with_cloud_capacity_management_technical_de)

### matrix-kernel-tiling-cost

- Query: `"matrix tiling" "workspace" interview coding Anthropic`
- Query: `site:1point3acres.com 矩阵 分块 roofline Anthropic 面经`
- Query: `site:prachub.com/interview-questions matrix tiling cost optimizer`
- Query: `GPU tile matrix memory traffic interview choose tile`
- Opened: [source](https://prachub.com/interview-questions/performance-model-a-sharded-matrix-multiply-flops-memory-network-and-roofline)

### batched-multihead-einsum-attention

- Query: `"einsum" "multi-head attention" interview numpy`
- Query: `site:1point3acres.com einsum 多头 注意力 面经`
- Query: `site:prachub.com/interview-questions multihead attention numpy einsum`
- Query: `"batched_multihead_attention" interview`
- Opened: [source](https://prachub.com/interview-questions/implement-the-forward-pass-of-multi-head-attention-from-scratch)
- Opened: [source](https://prachub.com/coding-questions/implement-and-analyze-custom-attention)

### pytorch-multihead-kv-cache

- Query: `"KV cache" "W_qkv" interview PyTorch MHA`
- Query: `site:1point3acres.com Anthropic kv cache 多头注意力 手撕`
- Query: `site:prachub.com/interview-questions implement multi head attention kv cache`
- Query: `"MHA(n_heads, dim)" "kv_cache"`
- Opened: [source](https://prachub.com/interview-questions/implement-multi-head-attention-with-a-kv-cache-and-cached-grouped-query-attention)
- Opened: [source](https://prachub.com/interview-questions/debug-a-transformer-implementation-and-implement-a-kv-cache-for-decoding)

### numpy-sigmoid-relu-network

- Query: `"sigmoid" "relu" "forward pass" numpy coding interview`
- Query: `site:1point3acres.com sigmoid relu 两层 神经网络 面经`
- Query: `site:prachub.com/interview-questions sigmoid relu network forward pass`
- Query: `"nn(x, W1, W2, b1, b2)" interview`
