package com.jin.gateway.dto;

/** FastAPI GET /api/v1/portfolio 응답과 필드명이 동일하다. */
public record StockQuote(String ticker, String name, long price, double changePercent) {
}
