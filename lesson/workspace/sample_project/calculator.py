"""Tiny sample module for the local agent to inspect."""


def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def divide(a, b):
    # Intentional bug for lesson 7: this should reject division by zero clearly.
    return a / b


def average(numbers):
    return sum(numbers) / len(numbers)

