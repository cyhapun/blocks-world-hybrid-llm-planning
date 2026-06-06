(define (problem bw_hard_010)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table a)
    (on_table c)
    (on_table e)
    (on b a)
    (on d c)
    (on f e)
    (clear b)
    (clear d)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on f b)
      (on d a)
    )
  )
)
