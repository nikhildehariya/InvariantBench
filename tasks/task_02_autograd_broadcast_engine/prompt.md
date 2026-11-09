# Task 02: Reverse-Mode Autodiff Engine with Broadcast Invariants

## Problem Description
Frontier code models frequently fail when implementing reverse-mode automatic differentiation engines because tensor broadcasting alters shapes dynamically. During backpropagation, any dimension that was expanded or broadcast in the forward pass must be summed out (reduced) in the backward pass.

Implement a computation graph `Tensor` class with reverse-mode automatic differentiation:

### Requirements:
1. **`Tensor(data, requires_grad=False)`**:
   - Stores `data` as a `numpy.ndarray` (float64).
   - Initializes `grad` as `None` (or zeros matching `data.shape` after backward).
   - Tracks DAG parents (`_prev`) and backward function (`_backward`).

2. **Operations Supported**:
   - `__add__(self, other)`: Elementwise addition supporting NumPy broadcasting.
   - `__mul__(self, other)`: Elementwise multiplication supporting NumPy broadcasting.
   - `matmul(self, other)`: Matrix multiplication (2D @ 2D).
   - `relu(self)`: $\max(0, x)$ non-linearity.
   - `sum(self, axis=None, keepdims=False)`: Tensor reduction.

3. **Autodiff & Mathematical Invariants**:
   - **Multi-Branch Gradient Accumulation:** If a tensor node is used multiple times in the expression graph (e.g., $y = x * x + x$), gradients flowing back from all branches MUST accumulate (`grad += ...`), not overwrite.
   - **Broadcast Gradient Reduction Invariant:** When $A + B$ or $A * B$ involves broadcasting (e.g., shape `(3, 4)` with shape `(4,)` or `(3, 1)`):
     - The gradient with respect to the smaller operand must sum across the broadcasted axes so that `operand.grad.shape == operand.data.shape`.
   - **Topological Backward Pass:** Calling `loss.backward()` must topologically sort the DAG and execute reverse-mode adjoint accumulation deterministically without infinite loops.
