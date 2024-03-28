from decimal import Decimal


class Node:
    def __init__(
        self,
        name,
        friendly_name=None,
        weight=None,
        children=None,
        account_value=0,
        weight_strategy="equal",
        specified_weights=None,
        selection_function=None,
        **kwargs,
    ):
        self.name = name
        self.friendly_name = friendly_name or name
        self.weight = weight
        self.children = children or []
        self.account_value = account_value
        self.weight_strategy = weight_strategy
        self.specified_weights = specified_weights or {}
        self.selection_function = selection_function
        self.additional_attributes = kwargs
        self.selected_children = self.children  # Default to all children

    def apply_weighting_strategy(self):
        if callable(self.selection_function):
            self.selected_children = self.selection_function(self.children)
        else:
            self.selected_children = self.children

        if self.weight_strategy == "equal":
            self.set_equal_weight()
        elif self.weight_strategy == "specified":
            self.set_specified_weights(self.specified_weights)
        elif self.weight_strategy == "inverse-volatility":
            # TODO: inverse volatility weighting
            self.set_equal_weight()
        else:
            raise ValueError(f"Unknown weighting strategy: {self.weight_strategy}")

        self.calculate_allocated_values()

    def set_equal_weight(self):
        if self.selected_children:
            equal_weight = 100 / len(self.selected_children)
            for child in self.selected_children:
                child.weight = equal_weight

    def set_specified_weights(self, weights_dict):
        self.specified_weights = weights_dict
        total_weight = sum(weights_dict.values())
        if total_weight > 100:
            raise ValueError("Total weight must not exceed 100%")

        for child in self.children:
            if child.name in weights_dict:
                child.weight = weights_dict[child.name]
            else:
                raise ValueError(f"Weight not specified for '{child.name}'")

    def add_child(self, child_node):
        self.children.append(child_node)

    def apply_strategy(self):
        self.apply_weighting_strategy()

    def set_account_value(self, value):
        self.account_value = value
        self.apply_weighting_strategy()

    def calculate_allocated_values(self):
        total_allocated = 0
        for child in self.selected_children:
            child.account_value = (child.weight / 100) * self.account_value
            total_allocated += child.account_value
            child.calculate_allocated_values()
        # Adjust for rounding errors
        if self.children and total_allocated != self.account_value:
            self.children[-1].account_value += self.account_value - total_allocated

    def get_additional_attribute(self, attr):
        return self.additional_attributes.get(attr)

    def get_weight_distribution(self, level=0):
        indent = "  " * level
        distribution = f"{indent}{self.friendly_name} (Weight: {self.weight}%, Value: ${self.account_value:.2f})\n"
        for child in self.selected_children:
            distribution += child.get_weight_distribution(level + 1)
        return distribution

    def __str__(self):
        return self.get_weight_distribution()


# And your custom selection function can access these attributes:
def select_top_by_returns(children, top_n=2):
    sorted_children = sorted(
        children, key=lambda x: x.get_additional_attribute("returns"), reverse=True
    )
    return sorted_children[:top_n]


if __name__ == "__main__":
    # Example Usage
    root = Node("Portfolio", weight=100, account_value=10000)

    # Tech Stocks Group with custom selection function
    tech_group = Node(
        "Tech Stocks",
        selection_function=lambda children: select_top_by_returns(children, top_n=2),
    )
    # Add children with mock 'returns' attribute
    tech_group.add_child(Node("Apple", returns=10))
    tech_group.add_child(Node("Google", returns=15))
    tech_group.add_child(Node("Microsoft", returns=12))

    # Healthcare Stocks Group
    healthcare_group = Node("Healthcare Stocks", weight_distribution_strategy="equal")
    healthcare_group.add_child(Node("Pfizer"))
    healthcare_group.add_child(Node("Johnson & Johnson"))
    healthcare_group.add_child(Node("Moderna"))

    # Adding groups to root
    root.add_child(tech_group)
    root.add_child(healthcare_group)

    # Apply the strategies to the groups
    tech_group.apply_strategy()
    healthcare_group.apply_strategy()
    root.apply_strategy()

    print(root)
