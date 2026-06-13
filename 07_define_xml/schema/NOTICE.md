# Vendored CDISC schema bundle (Define-XML 2.1 + ARM 1.0 + ODM 1.3.2)

These `.xsd` files are the **official CDISC Define-XML 2.1 schema bundle** (with the ODM 1.3.2
foundation and ARM 1.0 extension), vendored here **unmodified** so that `define.xml` can be
validated offline and reproducibly — `schema.cdisc.org` is not always reachable from CI.

- Entry schema for an ARM-bearing define: `cdisc-arm-1.0/arm-extension.xsd`
  (redefines `cdisc-define-2.1/define-extension.xsd` to add `arm:AnalysisResultDisplays`).
- Validate: `07_define_xml/validate_xsd.sh` (wraps `xmllint --noout --schema …`).

CDISC publishes these schemas for use in producing/validating Define-XML; they are redistributed
here solely for offline validation of this repository's metadata. Source: CDISC Define-XML 2.1
package (cdisc-define-2.1 / cdisc-odm-1.3.2 / cdisc-arm-1.0).
