(define (problem bw_hard_014)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table c)
    (on_table d)
    (on_table e)
    (on a c)
    (on b a)
    (on f e)
    (clear b)
    (clear d)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on d b)
      (on f a)
    )
  )
)
