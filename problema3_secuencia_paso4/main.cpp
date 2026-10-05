#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string_view>
#include <system_error>

void function(const std::uint64_t n) {
    for (std::uint64_t i = 1; i <= n / 3; ++i) {
        for (std::uint64_t j = 1; j <= n; j += 4) {
            std::printf("Sequence\n");
        }
    }
}

std::uint64_t leer_entero(const std::string_view texto) {
    std::uint64_t valor = 0;
    const auto resultado = std::from_chars(texto.data(), texto.data() + texto.size(), valor);
    if (texto.empty() || resultado.ec != std::errc{} ||
        resultado.ptr != texto.data() + texto.size() || valor == 0 || valor > 1'000'000) {
        throw std::invalid_argument("Se requiere un entero entre 1 y 1000000.");
    }
    return valor;
}

int main(const int argc, char* argv[]) {
    try {
        if (argc != 2 && argc != 3 && argc != 5) {
            throw std::invalid_argument("Uso: programa N [--profile [--repeticiones R]].");
        }
        const std::uint64_t n = leer_entero(argv[1]);
        const bool profiling = argc >= 3;
        if (profiling && std::string_view{argv[2]} != "--profile") {
            throw std::invalid_argument("La opción válida es --profile.");
        }
        std::uint64_t repeticiones = 1;
        if (argc == 5) {
            if (std::string_view{argv[3]} != "--repeticiones") {
                throw std::invalid_argument("La opción válida es --repeticiones.");
            }
            repeticiones = leer_entero(argv[4]);
        }
        const auto inicio = std::chrono::steady_clock::now();
        for (std::uint64_t r = 0; r < repeticiones; ++r) {
            function(n);
        }
        if (std::fflush(stdout) != 0 || std::ferror(stdout) != 0) {
            throw std::runtime_error("No se pudo escribir la salida.");
        }
        const auto fin = std::chrono::steady_clock::now();
        if (profiling) {
            const double segundos = std::chrono::duration<double>(fin - inicio).count();
            std::cerr << std::setprecision(17)
                      << segundos / static_cast<double>(repeticiones) << '\n';
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Error: " << error.what() << '\n';
        return 1;
    }
}
