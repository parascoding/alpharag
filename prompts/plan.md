Design and develop a **RAG-enabled stock market prediction system** targeting the Indian equity market. This project will require you to build an end-to-end solution from scratch, integrating various components to deliver a robust and actionable tool. The core of this system will be a Large Language Model (LLM) that leverages Retrieval-Augmented Generation (RAG) to provide nuanced, data-driven insights.

## Core Functionality

Your system must perform the following actions:

  * **Market Data Ingestion:**

      * Retrieve the **latest real-time and historical market data** for the Indian stock market (NSE & BSE).
      * Prioritize the use of **free APIs** (e.g., Alpha Vantage, Finnhub, or similar) whenever possible.
      * In cases where a free API for specific data (e.g., intraday or extensive historical data) is not available, create a provision for the user to **manually upload data** via a structured file format (e.g., CSV).

  * **User Portfolio Integration:**

      * Design a mechanism to get a user's current portfolio details (holdings, buy price, quantity, etc.).
      * Since free APIs for this are limited, this functionality must rely on **user-provided data** via a file upload.

  * **News and Sentiment Analysis:**

      * Utilize **free APIs** to gather the latest news and relevant financial headlines related to the Indian equity market and specific stocks.
      * This component should also perform a **sentiment analysis** on the collected news to identify positive, negative, or neutral sentiment, which will serve as a key input for the prediction model.

  * **Performance Prediction and Rationale Generation:**

      * Using the ingested market data, user portfolio details, and news sentiment, the LLM must **predict the potential performance** of the stocks in the user's portfolio.
      * The prediction should not just be a numerical output but also include a **descriptive rationale** based on the RAG framework. This means the LLM should retrieve relevant context from the ingested data and news articles to explain *why* a particular prediction was made. For example, "Stock X is predicted to rise due to positive Q3 earnings reports and a recent government policy announcement that benefits the sector."

  * **Automated Communication:**

      * Based on the predictions, the system must generate and send an **email to the user**.
      * The email should outline a clear **"call to action"** for each stock: "Buy," "Sell," or "Hold."
      * If no action is recommended, the email should explicitly state, "No action to take."
      * This communication should be powered by a **free email API service** (e.g., Mailjet, SendGrid free tier).

## Development Instructions

Your implementation should be a complete, runnable solution. The LLM must be a central part of this system, not just a final output generator. It must be able to reason, synthesize information from multiple sources, and present its findings in a coherent, actionable format.

This video provides a practical guide on getting real-time Indian stock market data for free using Python, which is a crucial first step for this project.