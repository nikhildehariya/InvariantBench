"""Test suite for Task 02: Reverse-Mode Autodiff Engine."""

import time
from typing import List
import numpy as np
from eval_suite.models import TestCaseResult, TestStatus


def run_task_tests(candidate_module) -> List[TestCaseResult]:
    results = []
    TensorClass = getattr(candidate_module, "Tensor", None)

    if TensorClass is None:
        results.append(
            TestCaseResult(
                name="class_exists",
                status=TestStatus.FAIL,
                duration_ms=0.0,
                message="Tensor class not defined in candidate module",
            )
        )
        return results

    # Test 1: Basic Scalar Differentiation
    def _test_scalar():
        # y = 3 * x^2 + 2 * x + 1 at x = 3. dy/dx = 6*x + 2 = 20
        x = TensorClass(3.0, requires_grad=True)
        y = TensorClass(3.0) * (x * x) + TensorClass(2.0) * x + TensorClass(1.0)
        y.backward()
        assert x.grad is not None, "x.grad is None"
        assert np.isclose(x.grad, 20.0), f"Expected gradient 20.0, got {x.grad}"

    t0 = time.perf_counter()
    try:
        _test_scalar()
        results.append(TestCaseResult("test_basic_scalar_autodiff", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_basic_scalar_autodiff", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 2: Multi-Branch Gradient Accumulation (x reused across branches)
    def _test_multi_branch():
        # y = (x * x) + x at x = 4.0. dy/dx = 2*x + 1 = 9.0
        x = TensorClass(4.0, requires_grad=True)
        y = (x * x) + x
        y.backward()
        assert x.grad is not None, "x.grad is None"
        assert np.isclose(x.grad, 9.0), f"Gradient overwrite trap detected! Expected 9.0, got {x.grad}"

    t0 = time.perf_counter()
    try:
        _test_multi_branch()
        results.append(TestCaseResult("test_multi_branch_gradient_accumulation", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_multi_branch_gradient_accumulation", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 3: Broadcast Addition Gradient Reduction Invariant
    def _test_broadcast_add():
        # A shape (3, 4), B shape (4,)
        A_data = np.arange(12, dtype=np.float64).reshape(3, 4)
        B_data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)

        A = TensorClass(A_data, requires_grad=True)
        B = TensorClass(B_data, requires_grad=True)
        C = (A + B).sum()
        C.backward()

        assert B.grad is not None, "B.grad is None"
        assert B.grad.shape == (4,), (
            f"Broadcast Invariant Violation: B.grad.shape is {B.grad.shape}, "
            f"expected reduced shape (4,)"
        )
        assert np.allclose(B.grad, np.array([3.0, 3.0, 3.0, 3.0])), (
            f"B.grad values incorrect: {B.grad}"
        )

    t0 = time.perf_counter()
    try:
        _test_broadcast_add()
        results.append(TestCaseResult("test_broadcast_add_reduction", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_broadcast_add_reduction", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 4: Broadcast Multiplication with Finite Difference Numerical Gradcheck
    def _test_numerical_gradcheck():
        eps = 1e-5
        # A: (2, 3), B: (1, 3)
        A_val = np.array([[1.5, 2.0, -1.0], [0.5, -2.5, 3.0]], dtype=np.float64)
        B_val = np.array([[2.0, -1.0, 4.0]], dtype=np.float64)

        # Analytical backward
        A = TensorClass(A_val, requires_grad=True)
        B = TensorClass(B_val, requires_grad=True)
        loss = (A * B).sum()
        loss.backward()

        analytical_B_grad = B.grad.copy()
        assert analytical_B_grad.shape == (1, 3), f"B grad shape mismatch: {analytical_B_grad.shape}"

        # Finite difference check for each element of B
        numerical_B_grad = np.zeros_like(B_val)
        for i in range(B_val.shape[0]):
            for j in range(B_val.shape[1]):
                B_plus = B_val.copy()
                B_plus[i, j] += eps
                loss_plus = np.sum(A_val * B_plus)

                B_minus = B_val.copy()
                B_minus[i, j] -= eps
                loss_minus = np.sum(A_val * B_minus)

                numerical_B_grad[i, j] = (loss_plus - loss_minus) / (2 * eps)

        assert np.allclose(analytical_B_grad, numerical_B_grad, atol=1e-4), (
            f"Numerical gradcheck failed! Analytical:\n{analytical_B_grad}\nNumerical:\n{numerical_B_grad}"
        )

    t0 = time.perf_counter()
    try:
        _test_numerical_gradcheck()
        results.append(TestCaseResult("test_numerical_gradcheck", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_numerical_gradcheck", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 5: MatMul Gradient Correctness  -  Chain Rule for Bilinear Map
    def _test_matmul_grad():
        # Z = X @ W, loss = sum(Z). dL/dX = ones @ W.T, dL/dW = X.T @ ones
        X_val = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float64)
        W_val = np.array([[0.5, -1.0, 2.0], [1.5, 0.0, -0.5]], dtype=np.float64)

        X = TensorClass(X_val, requires_grad=True)
        W = TensorClass(W_val, requires_grad=True)
        Z = X.matmul(W)
        loss = Z.sum()
        loss.backward()

        ones_out = np.ones_like(Z.data)
        expected_dX = ones_out @ W_val.T
        expected_dW = X_val.T @ ones_out
        assert np.allclose(X.grad, expected_dX, atol=1e-10), f"dX mismatch: {X.grad} vs {expected_dX}"
        assert np.allclose(W.grad, expected_dW, atol=1e-10), f"dW mismatch: {W.grad} vs {expected_dW}"

    t0 = time.perf_counter()
    try:
        _test_matmul_grad()
        results.append(TestCaseResult("test_matmul_gradient_correctness", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_matmul_gradient_correctness", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    # Test 6: ReLU Dead Neuron  -  Zero Gradient Below Zero
    def _test_relu_dead_neuron():
        # For x < 0, relu(x) = 0, grad = 0 (dead neuron invariant)
        x_val = np.array([-3.0, 0.5, -1.0, 2.0], dtype=np.float64)
        x = TensorClass(x_val, requires_grad=True)
        y = x.relu()
        loss = y.sum()
        loss.backward()

        expected_grad = np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float64)
        assert np.allclose(x.grad, expected_grad, atol=1e-10), (
            f"ReLU dead neuron invariant violated! x.grad={x.grad}, expected={expected_grad}"
        )

    t0 = time.perf_counter()
    try:
        _test_relu_dead_neuron()
        results.append(TestCaseResult("test_relu_dead_neuron_zero_grad", TestStatus.PASS, (time.perf_counter() - t0) * 1000))
    except Exception as e:
        results.append(TestCaseResult("test_relu_dead_neuron_zero_grad", TestStatus.FAIL, (time.perf_counter() - t0) * 1000, str(e)))

    return results
