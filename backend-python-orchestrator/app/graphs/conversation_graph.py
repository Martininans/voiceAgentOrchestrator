from typing import Dict, Callable
from langgraph.graph import StateGraph, START, END


def build_graph(classify_fn: Callable[[Dict], Dict], act_fn: Callable[[Dict], Dict]):
    graph = StateGraph(dict)

    def classify(state: Dict) -> Dict:
        return classify_fn(state)

    def act(state: Dict) -> Dict:
        return act_fn(state)

    graph.add_node("classify", classify)
    graph.add_node("act", act)

    graph.add_edge(START, "classify")
    graph.add_edge("classify", "act")
    graph.add_edge("act", END)

    return graph.compile()













