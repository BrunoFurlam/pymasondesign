from __future__ import annotations

from typing import Iterable
from attrs import field, frozen


@frozen
class SectionForces:
    """Representa o conjunto de esforços solicitantes atuantes em uma seção transversal.

    Attributes:
        normal: Esforço normal (N), positivo para tração e negativo para compressão.
        moment_x: Momento fletor em torno do eixo baricêntrico X (Mx).
        moment_y: Momento fletor em torno do eixo baricêntrico Y (My).
        shear_x: Esforço cortante na direção X (Vx).
        shear_y: Esforço cortante na direção Y (Vy).
        torsion: Momento torsor (T).
    """

    normal: float = field(default=0.0, converter=float)
    moment_x: float = field(default=0.0, converter=float)
    moment_y: float = field(default=0.0, converter=float)
    shear_x: float = field(default=0.0, converter=float)
    shear_y: float = field(default=0.0, converter=float)
    torsion: float = field(default=0.0, converter=float)

    def scale(self, factor: float) -> SectionForces:
        """Retorna uma nova instância com todos os esforços multiplicados por um fator escalar."""
        return SectionForces(
            normal=self.normal * factor,
            moment_x=self.moment_x * factor,
            moment_y=self.moment_y * factor,
            shear_x=self.shear_x * factor,
            shear_y=self.shear_y * factor,
            torsion=self.torsion * factor,
        )

    def __add__(self, other: SectionForces) -> SectionForces:
        if not isinstance(other, SectionForces):
            return NotImplemented
        return SectionForces(
            normal=self.normal + other.normal,
            moment_x=self.moment_x + other.moment_x,
            moment_y=self.moment_y + other.moment_y,
            shear_x=self.shear_x + other.shear_x,
            shear_y=self.shear_y + other.shear_y,
            torsion=self.torsion + other.torsion,
        )

    def __mul__(self, factor: float) -> SectionForces:
        return self.scale(factor)

    def __rmul__(self, factor: float) -> SectionForces:
        return self.scale(factor)

    @classmethod
    def combine(cls, items: Iterable[SectionForces]) -> SectionForces:
        """Combina e totaliza múltiplos esforços solicitantes a partir de um iterável."""
        n = 0.0
        mx = 0.0
        my = 0.0
        vx = 0.0
        vy = 0.0
        t = 0.0
        for f in items:
            n += f.normal
            mx += f.moment_x
            my += f.moment_y
            vx += f.shear_x
            vy += f.shear_y
            t += f.torsion
        return cls(
            normal=n,
            moment_x=mx,
            moment_y=my,
            shear_x=vx,
            shear_y=vy,
            torsion=t,
        )
