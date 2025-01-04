# Real-time smart contract event processing using web3.py and asyncio
## Overview
This service listens for Ethereum events from multiple smart contracts and processes the events in real-time using Web3.py and asyncio. The code is built to be highly scalable and modular, making it a useful tool for monitoring and analyzing blockchain events, especially in the DeFi space. It can be easily extended to track various DeFi protocols (e.g., Uniswap, Aave, Compound, etc.), and it integrates with messaging systems (e.g., Kafka) for downstream processing.

## Key Features:
- **Asynchronous Event Listening**: It listens for Ethereum events asynchronously, enabling it to handle multiple contracts and events concurrently without blocking the execution.
- **Configurable Event Handling**: Supports dynamic event listening for multiple contracts based on configurations read from JSON files.
- **Graceful Shutdown**: It can handle graceful shutdowns, ensuring that all event listeners are properly closed when the application is stopped.
- **Scalability**: It's designed to scale for a large number of contract/event pairs by using asyncio's event loop and running listeners concurrently.
- **Event Publishing**: When an event is received, it can be processed and sent to other systems (like Kafka) for real-time analysis and reporting.
