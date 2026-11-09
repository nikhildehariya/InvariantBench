"""Buggy LLM Baseline Implementation for Task 02.

Representative of typical frontier LLM outputs:
1. Fails to reduce/sum gradients across broadcasted dimensions (e.g. adding (3, 4) + (4,)),
   leading to shape mismatches or corrupt gradient tensors.
2. Uses direct gradient assignment `self.grad = ...` instead of accumulating (`+=`),
   corrupting adjoints when a tensor is used in multiple computational paths.
"""

import numpy as np
from typing import Union, Optional, Tuple, Set


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

    def __add__(self, other) -> 'Tensor':
        if not isinstance(other, Tensor):
            other = Tensor(other)
        out = Tensor(self.data + other.data, requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            # LLM TRAP 1: Overwrites grad instead of accumulating
            # LLM TRAP 2: Ignores broadcasting! Assigns (3, 4) gradient directly to (4,) tensor!
            if self.requires_grad:
                self.grad = out.grad
            if other.requires_grad:
                other.grad = out.grad

        out._backward = _backward
        return out

    def __mul__(self, other) -> 'Tensor':
        if not isinstance(other, Tensor):
            other = Tensor(other)
        out = Tensor(self.data * other.data, requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            # LLM TRAP: Overwrites grad and fails broadcasting reduction
            if self.requires_grad:
                self.grad = out.grad * other.data
            if other.requires_grad:
                other.grad = out.grad * self.data

        out._backward = _backward
        return out

    def matmul(self, other: 'Tensor') -> 'Tensor':
        if not isinstance(other, Tensor):
            other = Tensor(other)
        out = Tensor(np.matmul(self.data, other.data), requires_grad=(self.requires_grad or other.requires_grad))
        out._prev = {self, other}

        def _backward():
            if self.requires_grad:
                self.grad = np.matmul(out.grad, other.data.T)
            if other.requires_grad:
                other.grad = np.matmul(self.data.T, out.grad)

        out._backward = _backward
        return out

    def relu(self) -> 'Tensor':
        out = Tensor(np.maximum(0, self.data), requires_grad=self.requires_grad)
        out._prev = {self}

        def _backward():
            if self.requires_grad:
                self.grad = out.grad * (self.data > 0).astype(np.float64)

        out._backward = _backward
        return out

    def sum(self, axis=None, keepdims=False) -> 'Tensor':
        out = Tensor(np.sum(self.data, axis=axis, keepdims=keepdims), requires_grad=self.requires_grad)
        out._prev = {self}

        def _backward():
            if self.requires_grad:
                self.grad = np.broadcast_to(out.grad, self.shape)

        out._backward = _backward
        return out

    def backward(self):
        if self.grad is None:
            self.grad = np.ones_like(self.data, dtype=np.float64)

        topo = []
        visited = set()

        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._prev:
                    build_topo(child)
                topo.append(v)

        build_topo(self)
        for node in reversed(topo):
            node._backward()
