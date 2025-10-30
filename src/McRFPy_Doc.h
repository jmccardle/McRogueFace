#ifndef MCRFPY_DOC_H
#define MCRFPY_DOC_H

// Section builders for documentation
#define MCRF_SIG(params, ret) params " -> " ret "\n\n"
#define MCRF_DESC(text) text "\n\n"
#define MCRF_ARGS_START "Args:\n"
#define MCRF_ARG(name, desc) "    " name ": " desc "\n"
#define MCRF_RETURNS(text) "\nReturns:\n    " text "\n"
#define MCRF_RAISES(exc, desc) "\nRaises:\n    " exc ": " desc "\n"
#define MCRF_NOTE(text) "\nNote:\n    " text "\n"

// Link to external documentation
// Format: MCRF_LINK("docs/file.md", "Link Text")
// Parsers detect this pattern and format per output type
#define MCRF_LINK(ref, text) "\nSee also: " text " (" ref ")\n"

// Main documentation macros
#define MCRF_METHOD_DOC(name, sig, desc, ...) \
    name sig desc __VA_ARGS__

#define MCRF_FUNCTION(name, ...) \
    MCRF_METHOD_DOC(#name, __VA_ARGS__)

#define MCRF_METHOD(cls, name, ...) \
    MCRF_METHOD_DOC(#name, __VA_ARGS__)

#define MCRF_PROPERTY(name, desc) \
    desc

#endif // MCRFPY_DOC_H
