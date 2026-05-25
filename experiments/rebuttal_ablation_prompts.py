"""
Alternative prompt orderings for the layer-ordering ablation.
Each ordering is strictly additive — each level appends to the previous.
"""

ABLATION_TEMPLATES: dict[str, dict[str, list[str]]] = {

    'classification': {
        'order_A_example_early': [
            # L1: bare
            "Classify: {text}",

            # L2: bare + worked example
            (
                "Classify the following text.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),

            # L3: + class names
            (
                "Classify sentiment as positive, negative, or neutral.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),

            # L4: + output format
            (
                "Classify sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),

            # L5: + definitions
            (
                "Classify the sentiment of the following text as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),

            # L6: + persona
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment of the following text as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),

            # L7: + guidelines
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment of the following text as positive, negative, or neutral.\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. Positive: clearly favorable, optimistic, praising, or satisfied\n"
                "4. Negative: clearly unfavorable, critical, pessimistic, or dissatisfied\n"
                "5. Neutral: factual reporting, balanced views, or no discernible sentiment\n"
                "6. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "7. Take text at face value; do not attempt sarcasm detection\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
        ],

        'order_B_definitions_early': [
            # L1: bare
            "Classify: {text}",

            # L2: bare + definitions
            (
                "Classify the text using these definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),

            # L3: + task label
            (
                "Classify sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),

            # L4: + format spec
            (
                "Classify sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),

            # L5: + persona
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral. "
                "Respond with only the label.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Text: {text}"
            ),

            # L6: + guidelines
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "4. Take text at face value; do not attempt sarcasm detection\n\n"
                "Text: {text}"
            ),

            # L7: + worked example
            (
                "You are a sentiment classification expert. "
                "Classify the sentiment as positive, negative, or neutral.\n\n"
                "Definitions:\n"
                "- positive: overall favorable or optimistic tone\n"
                "- negative: overall unfavorable or critical tone\n"
                "- neutral: balanced, factual, or no clear sentiment\n\n"
                "Rules:\n"
                "1. Respond with ONLY one word: positive, negative, or neutral\n"
                "2. Base your judgment on the overall tone, not individual words\n"
                "3. If mixed, choose the dominant sentiment; if equal, use neutral\n"
                "4. Take text at face value; do not attempt sarcasm detection\n\n"
                "Example:\n"
                "Text: The product works great and I'm very happy with my purchase.\n"
                "Label: positive\n\n"
                "Now classify:\n"
                "Text: {text}"
            ),
        ],
    },

    'product_extraction': {
        'order_A_example_early': [
            # L1: bare
            "Extract product info: {product_text}",

            # L2: bare + worked example
            (
                "Extract product information from the text below.\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),

            # L3: + field names
            (
                "Extract the product name, price, brand, and category from this text.\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),

            # L4: + JSON format
            (
                "Extract the product name, price, brand, and category from this text. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),

            # L5: + field definitions
            (
                "Extract the following fields from this product description. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),

            # L6: + persona + edge cases
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "If a field cannot be determined, use \"unknown\".\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),

            # L7: + detailed guidelines
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated in the text\n"
                "- price: numeric value only — strip currency symbols and commas\n"
                "- brand: the manufacturer, not the retailer or seller\n"
                "- category: a single general product type (e.g., 'laptop', 'headphones', 'shoes')\n\n"
                "Guidelines:\n"
                "- Use the exact product name as written in the text\n"
                "- If price is written in words, convert to digits\n"
                "- If brand is only in the product name, extract it from there\n"
                "- If a field cannot be determined, use \"unknown\"\n"
                "- Return ONLY valid JSON, no extra text\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),
        ],

        'order_B_definitions_early': [
            # L1: bare
            "Extract product info: {product_text}",

            # L2: bare + field definitions
            (
                "Extract the following fields from this product text:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "{product_text}"
            ),

            # L3: + field names + JSON format
            (
                "Extract the product name, price, brand, and category from this text. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "{product_text}"
            ),

            # L4: + persona
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "{product_text}"
            ),

            # L5: + edge case handling
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated\n"
                "- price: numeric value only (no currency symbols)\n"
                "- brand: the manufacturer or brand name\n"
                "- category: the general product type (one or two words)\n\n"
                "If a field cannot be determined, use \"unknown\".\n\n"
                "{product_text}"
            ),

            # L6: + detailed guidelines
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated in the text\n"
                "- price: numeric value only — strip currency symbols and commas\n"
                "- brand: the manufacturer, not the retailer or seller\n"
                "- category: a single general product type (e.g., 'laptop', 'headphones', 'shoes')\n\n"
                "Guidelines:\n"
                "- Use the exact product name as written in the text\n"
                "- If price is written in words, convert to digits\n"
                "- If brand is only in the product name, extract it from there\n"
                "- If a field cannot be determined, use \"unknown\"\n"
                "- Return ONLY valid JSON, no extra text\n\n"
                "{product_text}"
            ),

            # L7: + worked example
            (
                "You are a product data specialist. "
                "Extract structured information from the product description below. "
                "Return as JSON with keys: name, price, brand, category.\n\n"
                "Field definitions:\n"
                "- name: the full product name as stated in the text\n"
                "- price: numeric value only — strip currency symbols and commas\n"
                "- brand: the manufacturer, not the retailer or seller\n"
                "- category: a single general product type (e.g., 'laptop', 'headphones', 'shoes')\n\n"
                "Guidelines:\n"
                "- Use the exact product name as written in the text\n"
                "- If price is written in words, convert to digits\n"
                "- If brand is only in the product name, extract it from there\n"
                "- If a field cannot be determined, use \"unknown\"\n"
                "- Return ONLY valid JSON, no extra text\n\n"
                "Example:\n"
                "Text: The new Bose SoundLink Flex portable speaker offers 12 hours of battery "
                "life and IP67 waterproofing. Now available for $149.00.\n"
                "Output: {\"name\": \"Bose SoundLink Flex\", \"price\": \"149\", "
                "\"brand\": \"Bose\", \"category\": \"speaker\"}\n\n"
                "Now extract:\n"
                "{product_text}"
            ),
        ],
    },
}
