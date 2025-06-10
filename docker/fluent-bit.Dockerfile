FROM fluent/fluent-bit:latest


COPY ./services/fluent-bit/parsers.conf /fluent-bit/etc/parsers.conf
COPY ./services/fluent-bit/predications_lua.lua /fluent-bit/etc/predications_lua.lua
COPY ./services/fluent-bit/fluent-bit.conf /fluent-bit/etc/fluent-bit.conf
