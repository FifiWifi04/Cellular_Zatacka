#!/usr/bin/env node
// T29: minimal WebSocket relay for Cellular Zatacka's online lobby.
//
// This is the v1 transport (see docs/tasks/T29-net-transport-lobby.md
// Findings): a dumb per-room broadcast/relay, not a WebRTC signalling server.
// Peers never talk to each other directly -- every message passes through
// this process, tagged with the sender's id, and is either broadcast to the
// rest of the room or routed to a single `to` peer. The game (260703_Cellsnake.html)
// is the only client; this process has no game logic of its own.
//
// Run:  node tools/relay_server.js [port]      (default port 8090)
// Requires the `ws` package: `npm install` inside tools/ once before running.
'use strict';

const { WebSocketServer } = require('ws');

const PORT = parseInt(process.argv[2], 10) || 8090;
const PROTOCOL_VERSION = 1; // must match NET_PROTOCOL_VERSION in 260703_Cellsnake.html
const MAX_PLAYERS = 4; // playerConfigs in the game defines exactly four slots
const ROOM_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'; // no 0/O, no 1/I/L
const ROOM_CODE_LENGTH = 5;
// T32: how long a non-host peer's slot stays reclaimable by the same browser
// (identified by its persistent `cid`, not the per-connection peerId) after
// its WebSocket actually closes. Must match NET_GONE_MS in
// 260703_Cellsnake.html -- past this window the game's own heartbeat has
// already classified the peer 'gone' and handed it to the bot AI for good.
const REJOIN_WINDOW_MS = 15000;

const rooms = new Map(); // code -> { code, hostId, peers: Map<id, {ws, name, cid}>, departed: Map<cid, {peerId, name}> }
let nextPeerId = 1;

function makeRoomCode() {
    let code;
    do {
        code = '';
        for (let i = 0; i < ROOM_CODE_LENGTH; i++) {
            code += ROOM_CODE_ALPHABET[Math.floor(Math.random() * ROOM_CODE_ALPHABET.length)];
        }
    } while (rooms.has(code));
    return code;
}

function send(ws, obj) {
    if (ws.readyState === ws.OPEN) ws.send(JSON.stringify(obj));
}

function broadcastLobby(room) {
    let msg = {
        t: 'lobby',
        players: [...room.peers.entries()].map(([id, p]) => ({ id, name: p.name, isHost: id === room.hostId }))
    };
    for (const p of room.peers.values()) send(p.ws, msg);
}

// T32: broadcasts to every current member of a room, tagged from no one peer
// in particular -- used for 'peerRejoined', which every peer needs to see
// (only the host actually acts on it; see netHandlePeerRejoined()).
function broadcastRoom(room, msg) {
    for (const p of room.peers.values()) send(p.ws, msg);
}

// Application messages (start/input/state/ping/pong) never touch room
// membership -- just forward them, tagged with the real sender.
function relay(room, fromId, msg) {
    msg.from = fromId;
    if (msg.to != null) {
        let target = room.peers.get(msg.to);
        if (target) send(target.ws, msg);
        return;
    }
    for (const [id, p] of room.peers) {
        if (id !== fromId) send(p.ws, msg);
    }
}

function removePeer(room, id) {
    let peerInfo = room.peers.get(id);
    let wasHost = id === room.hostId;
    room.peers.delete(id);
    if (room.peers.size === 0) {
        rooms.delete(room.code);
        return;
    }
    if (wasHost) {
        // Host migration is out of scope (T32's own design doc, §3) -- the
        // round ends honestly for everyone instead of attempting a handoff.
        for (const p of room.peers.values()) send(p.ws, { t: 'hostLeft' });
        rooms.delete(room.code);
        return;
    }
    // T32: remember this cid for REJOIN_WINDOW_MS so a reconnecting client
    // (same browser, new WebSocket -> new peerId) can be recognised as the
    // same player instead of taking a fresh slot -- see the 'join' handling
    // below and netHandlePeerRejoined() in 260703_Cellsnake.html.
    if (peerInfo && peerInfo.cid) {
        room.departed.set(peerInfo.cid, { peerId: id, name: peerInfo.name });
        setTimeout(() => { room.departed.delete(peerInfo.cid); }, REJOIN_WINDOW_MS);
    }
    for (const p of room.peers.values()) send(p.ws, { t: 'peerLeft', id });
    broadcastLobby(room);
}

const wss = new WebSocketServer({ port: PORT });
console.log(`[relay] listening on ws://0.0.0.0:${PORT}`);

wss.on('connection', ws => {
    let peerId = null;
    let room = null;

    ws.on('message', raw => {
        let msg;
        try { msg = JSON.parse(raw); } catch (e) { return; }

        if (msg.t === 'create' || msg.t === 'join') {
            if (msg.v !== PROTOCOL_VERSION) {
                send(ws, { t: 'joinError', reason: `Protocol version mismatch (client v${msg.v}, relay v${PROTOCOL_VERSION}). Reload both.` });
                ws.close();
                return;
            }
            let name = String(msg.name || 'Player').slice(0, 16);
            peerId = nextPeerId++;

            let cid = msg.cid || null;
            let rejoined = null; // T32: {peerId, name} of the departed slot this cid is reclaiming, if any

            if (msg.t === 'create') {
                let code = makeRoomCode();
                room = { code, hostId: peerId, peers: new Map(), departed: new Map() };
                rooms.set(code, room);
                room.peers.set(peerId, { ws, name, cid });
                send(ws, { t: 'created', room: code, id: peerId });
            } else {
                room = rooms.get(String(msg.room || '').toUpperCase());
                if (!room) { send(ws, { t: 'joinError', reason: 'No room with that code.' }); room = null; peerId = null; return; }
                if (room.peers.size >= MAX_PLAYERS) { send(ws, { t: 'joinError', reason: 'Room is full (max 4 players).' }); room = null; peerId = null; return; }
                if (cid && room.departed.has(cid)) {
                    rejoined = room.departed.get(cid);
                    room.departed.delete(cid);
                }
                room.peers.set(peerId, { ws, name, cid });
                send(ws, { t: 'joined', room: room.code, id: peerId, host: room.hostId, rejoinedAs: rejoined ? rejoined.peerId : undefined });
            }
            broadcastLobby(room);
            // T32: after the lobby update, so a rejoining host-side listener's
            // roster remap (netHandlePeerRejoined()) sees a room.peers list that
            // already includes the new connection.
            if (rejoined) broadcastRoom(room, { t: 'peerRejoined', oldId: rejoined.peerId, newId: peerId });
            return;
        }

        if (msg.t === 'bye') { ws.close(); return; }

        if (room && peerId != null) relay(room, peerId, msg);
    });

    ws.on('close', () => {
        if (room && peerId != null) removePeer(room, peerId);
    });
});
