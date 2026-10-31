class TrieNode:
    def __init__(self):
        self.children = {}
        self.category = None

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, category):
        node = self.root
        for ch in word.lower():
            node = node.children.setdefault(ch, TrieNode())
        node.category = category

    def categorize(self, text, default="Other"):
        text = text.lower()
        for i in range(len(text)):
            if i > 0 and text[i - 1].isalnum():
                continue          # match only at the start of a word
            node = self.root
            for ch in text[i:]:
                node = node.children.get(ch)
                if node is None:
                    break
                if node.category:
                    return node.category
        return default

KEYWORDS = {
    "Food": ["swiggy", "zomato", "restaurant", "cafe", "dominos", "mcdonald",
             "bigbasket", "grocery", "bakery", "blinkit", "zepto"],
    "Travel": ["uber", "ola", "rapido", "irctc", "redbus", "makemytrip",
               "petrol", "fuel", "metro", "fastag"],
    "Bills": ["electricity", "airtel", "jio", "vodafone", "recharge",
              "broadband", "insurance", "rent"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho", "mall"],
    "Health": ["pharmacy", "apollo", "medplus", "hospital", "clinic",
               "diagnostic", "netmeds"],
    "Salary": ["salary", "payroll", "stipend"],
}

def build_default_trie():
    trie = Trie()
    for category, words in KEYWORDS.items():
        for w in words:
            trie.insert(w, category)
    return trie