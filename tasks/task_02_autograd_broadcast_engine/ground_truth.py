"""Ground Truth Reference Implementation for Task 02: Reverse-Mode Autodiff Engine."""

import numpy as np
from typing import Union, Optional, Tuple, Set, List


def _unbroadcast(grad: np.ndarray, target_shape: Tuple[int, ...]) -> np.ndarray:
    """Sum out broadcasted dimensions so grad matches target_shape."""
    if grad.shape == target_shape:
        return grad

    grad_ndim = grad.ndim
    target_ndim = len(target_shape)

    # Sum along leading dimensions if grad has more dimensions
    if grad_ndim > target_ndim:
        axes_to_sum = tuple(range(grad_ndim - target_ndim))
        grad = grad.sum(axis=axes_to_sum)

    # Now grad.ndim == target_ndim. Sum along dimensions where target was 1
    axes_to_sum = []
    for i, (g_dim, t_dim) in enumerate(zip(grad.shape, target_shape)):
        if t_dim == 1 and g_dim > 1:
            axes_to_sum.append(i)

    if axes_to_sum:
        grad = grad.sum(axis=tuple(axes_to_sum), keepdims=True)

    return grad.reshape(target_shape)


class Tensor:
    def __init__(self, data: Union[int, float, list, np.ndarray], requires_grad: bool = False):
        self.data = np.asarray(data, dtype=np.float64)
        self.requires_grad = requires_grad
        self.grad: Optional[np.ndarray] = None
        self._prev: Set['Tensor'] = set()
        self._backward = lambda: None

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape

    def __repr__(self) -> str:
        return f"Tensor({self.data}, requires_grad={self.requires_grad})"

    def _ensure_tensor(self, other) -> 'Tensor':
        if isinstance(other, Tensor):
            return other
        return Tensor(other)

    def __add__(self, other) -> 'Tensor':
        other = self._ensure_tensor(other)
        out = Tensor(self.data + other.data, requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            if self.requires_grad:
                g_self = _unbroadcast(out.grad, self.shape)
                self.grad = g_self if self.grad is None else self.grad + g_self
            if other.requires_grad:
                g_other = _unbroadcast(out.grad, other.shape)
                other.grad = g_other if other.grad is None else other.grad + g_other

        out._backward = _backward
        return out

    def __mul__(self, other) -> 'Tensor':
        other = self._ensure_tensor(other)
        out = Tensor(self.data * other.data, requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            if self.requires_grad:
                g_self = _unbroadcast(out.grad * other.data, self.shape)
                self.grad = g_self if self.grad is None else self.grad + g_self
            if other.requires_grad:
                g_other = _unbroadcast(out.grad * self.data, other.shape)
                other.grad = g_other if other.grad is None else other.grad + g_other

        out._backward = _backward
        return out

    def matmul(self, other: 'Tensor') -> 'Tensor':
        other = self._ensure_tensor(other)
        out = Tensor(np.matmul(self.data, other.data), requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            if self.requires_grad:
                g_self = np.matmul(out.grad, other.data.T)
                self.grad = g_self if self.grad is None else self.grad + g_self
            if other.requires_grad:
                g_other = np.matmul(self.data.T, out.grad)
                other.grad = g_other if other.grad is None else other.grad + g_other

        out._backward = _backward
        return out

    def relu(self) -> 'Tensor':
        out = Tensor(np.maximum(0, self.data), requires_grad=self.requires_grad)
        out._prev = {self}

        def _backward():
            if self.requires_grad:
                g_self = out.grad * (self.data > 0).astype(np.float64)
                self.grad = g_self if self.grad is None else self.grad + g_self

        out._backward = _backward
        return out

    def sum(self, axis=None, keepdims=False) -> 'Tensor':
        out = Tensor(np.sum(self.data, axis=axis, keepdims=keepdims), requires_grad=self.requires_grad)
        out._prev = {self}

        def _backward():
            if self.requires_grad:
                if out.grad.ndim == 0 or not keepdims:
                    # broadcast scalar grad or reduced axes back to self.shape
                    expanded_grad = np.broadcast_to(out.grad, self.shape)
                else:
                    expanded_grad = out.grad
                self.grad = expanded_grad if self.grad is None else self.grad + expanded_grad

        out._backward = _backward
        return out

    def backward(self):
        if self.grad is None:
            self.grad = np.ones_like(self.data, dtype=np.float64)

        # Build topological ordering of DAG
        topo: List['Tensor'] = []
        visited: Set['Tensor'] = set()

        def build_topo(v: 'Tensor'):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)

        # Backpropagate in reverse topological order
        for node in reversed(topo):
            node._backward()
