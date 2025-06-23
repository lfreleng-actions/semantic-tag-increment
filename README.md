<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 🛠️ Template Action

This is a template for the other actions in this Github organisation.

## actions-template

## Usage Example

<!-- markdownlint-disable MD046 -->

```yaml
steps:
  - name: "Action template"
    id: action-template
    uses: lfreleng-actions/actions-template@main
    with:
      input: "placeholder"
```

<!-- markdownlint-enable MD046 -->

## Inputs

<!-- markdownlint-disable MD013 -->

| Name      | Required | Default     | Description                                   |
| --------- | -------- | ----------- | --------------------------------------------- |
| tag       | True     |             | Tag string to increment                       |
| increment | False    | dev         | Tag level to increment: major/minor/patch/dev |
| type      | False    | development | Incremented tag type: production/development  |

<!-- markdownlint-enable MD013 -->

## Outputs

<!-- markdownlint-disable MD013 -->

| Name        | Description                            |
| ----------- | -------------------------------------- |
| tag         | Incremented tag string                 |
| numeric_tag | Numeric tag stripped of any v/V prefix |

<!-- markdownlint-enable MD013 -->

Note: if the provided tag has no leading v/V character prefix, the tag and
numeric_tag output values will be identical.
