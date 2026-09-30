package com.jin.gateway.controller;

import com.jin.gateway.dto.ChatRequest;
import com.jin.gateway.dto.ChatResponse;
import com.jin.gateway.service.AiGatewayService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;

@RestController
@RequestMapping("/api/chat")
public class ChatController {

    private final AiGatewayService gateway;

    public ChatController(AiGatewayService gateway) {
        this.gateway = gateway;
    }

    @PostMapping
    public ChatResponse chat(@Valid @RequestBody ChatRequest req) {
        return gateway.chat(req);
    }

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ServerSentEvent<String>> stream(@Valid @RequestBody ChatRequest req) {
        return gateway.stream(req);
    }
}
